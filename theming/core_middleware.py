"""
Middleware for theme security and rate limiting.

This middleware provides security validation and rate limiting
for theme-related API endpoints.
"""

import json
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.utils import timezone
from .security import request_validator, rate_limiter

logger = logging.getLogger(__name__)


class ThemeSecurityMiddleware(MiddlewareMixin):
    """
    Middleware to provide security validation for theme API endpoints.
    
    This middleware validates requests to theme endpoints and blocks
    potentially malicious requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.theme_paths = [
            '/theming/api/v1/',
            '/api/v1/themes/',
            '/api/v1/events/',
        ]
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming requests for security validation."""
        
        # Only validate theme-related endpoints
        if not any(request.path.startswith(path) for path in self.theme_paths):
            return None
        
        # Skip validation for safe methods unless it's a file upload
        if request.method in ['GET', 'HEAD', 'OPTIONS'] and 'multipart/form-data' not in request.content_type:
            return None
        
        try:
            # Validate request security
            validation_result = request_validator.validate_request(request)
            
            if not validation_result['is_valid']:
                logger.warning(f"Blocked insecure request from {request.META.get('REMOTE_ADDR')}: {validation_result['warnings']}")
                return JsonResponse({
                    'error': 'Request blocked for security reasons',
                    'details': validation_result['warnings']
                }, status=400)
            
            # Log warnings for monitoring
            if validation_result['warnings']:
                logger.info(f"Security warnings for request from {request.META.get('REMOTE_ADDR')}: {validation_result['warnings']}")
            
            # Add security score to request for later use
            request.security_score = validation_result['security_score']
            
        except Exception as e:
            logger.error(f"Security validation error: {str(e)}")
            # Don't block request on validation errors, just log
            request.security_score = 50  # Neutral score
        
        return None
    
    def process_response(self, request, response):
        """Process responses to add security headers."""
        
        # Only add headers to theme API responses
        if any(request.path.startswith(path) for path in self.theme_paths):
            # Add security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Add custom security score header for monitoring
            if hasattr(request, 'security_score'):
                response['X-Security-Score'] = str(request.security_score)
        
        return response


class ThemeRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware to provide rate limiting for theme operations.
    
    This middleware implements rate limiting for resource-intensive
    theme operations to prevent abuse.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limited_endpoints = {
            '/theming/api/v1/events/': 'theme_generation',
            '/theming/api/v1/themes/': 'api_requests',
            'extract-colors': 'color_extraction',
            'generate': 'theme_generation',
        }
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process requests for rate limiting."""
        
        # Skip rate limiting for unauthenticated users (they have other limits)
        if not request.user.is_authenticated:
            return None
        
        # Skip rate limiting for staff users
        if request.user.is_staff:
            return None
        
        # Skip rate limiting for safe methods
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return None
        
        # Determine operation type based on URL
        operation_type = self._get_operation_type(request.path, request.method)
        if not operation_type:
            return None
        
        try:
            # Check rate limit
            rate_limit_result = rate_limiter.is_allowed(request.user.id, operation_type)
            
            if not rate_limit_result['allowed']:
                logger.warning(f"Rate limit exceeded for user {request.user.id} on operation {operation_type}")
                
                response = JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many {operation_type} requests',
                    'limit': rate_limit_result['limit'],
                    'period': rate_limit_result['period'],
                    'retry_after': int(rate_limit_result['retry_after'])
                }, status=429)
                
                # Add rate limit headers
                response['X-RateLimit-Limit'] = str(rate_limit_result['limit'])
                response['X-RateLimit-Remaining'] = str(rate_limit_result['limit'] - rate_limit_result['current_count'])
                response['X-RateLimit-Reset'] = str(int(rate_limit_result['reset_time']))
                response['Retry-After'] = str(int(rate_limit_result['retry_after']))
                
                return response
            
            # Add rate limit info to request for later use
            request.rate_limit_info = rate_limit_result
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # Don't block request on rate limiting errors
        
        return None
    
    def process_response(self, request, response):
        """Process responses to add rate limit headers."""
        
        # Add rate limit headers if available
        if hasattr(request, 'rate_limit_info') and request.user.is_authenticated:
            info = request.rate_limit_info
            response['X-RateLimit-Limit'] = str(info['limit'])
            response['X-RateLimit-Remaining'] = str(info['limit'] - info['current_count'])
            response['X-RateLimit-Reset'] = str(int(info['reset_time']))
        
        return response
    
    def _get_operation_type(self, path: str, method: str) -> str:
        """Determine the operation type based on URL path and method."""
        
        # Check for specific endpoints
        for endpoint, operation in self.rate_limited_endpoints.items():
            if endpoint in path:
                return operation
        
        # Default based on method
        if method == 'POST':
            if 'extract-colors' in path:
                return 'color_extraction'
            elif 'generate' in path:
                return 'theme_generation'
            else:
                return 'api_requests'
        
        return 'api_requests'


class ThemeAnalyticsMiddleware(MiddlewareMixin):
    """
    Middleware to collect analytics for theme operations.
    
    This middleware collects usage statistics and performance
    metrics for theme-related operations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.analytics_paths = [
            '/theming/api/v1/',
            '/theming/event/',
        ]
        super().__init__(get_response)
    
    def process_request(self, request):
        """Record request start time for performance tracking."""
        if any(request.path.startswith(path) for path in self.analytics_paths):
            request.theme_request_start = timezone.now()
        return None
    
    def process_response(self, request, response):
        """Record analytics data for theme operations."""
        
        # Only track theme-related requests
        if not any(request.path.startswith(path) for path in self.analytics_paths):
            return response
        
        # Skip tracking for certain methods
        if request.method in ['HEAD', 'OPTIONS']:
            return response
        
        try:
            # Calculate response time
            response_time = None
            if hasattr(request, 'theme_request_start'):
                response_time = (timezone.now() - request.theme_request_start).total_seconds() * 1000
            
            # Collect analytics data
            analytics_data = {
                'timestamp': timezone.now().isoformat(),
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self._get_client_ip(request),
                'content_length': len(response.content) if hasattr(response, 'content') else 0,
            }
            
            # Add security score if available
            if hasattr(request, 'security_score'):
                analytics_data['security_score'] = request.security_score
            
            # Store analytics data (in production, this would go to a proper analytics system)
            self._store_analytics_data(analytics_data)
            
        except Exception as e:
            logger.error(f"Analytics collection error: {str(e)}")
        
        return response
    
    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _store_analytics_data(self, data):
        """Store analytics data (simplified implementation)."""
        # In production, this would send data to an analytics service
        # For now, we'll store in cache with a short TTL
        cache_key = f"theme_analytics_{timezone.now().strftime('%Y%m%d_%H')}"
        analytics_list = cache.get(cache_key, [])
        analytics_list.append(data)
        
        # Keep only last 1000 entries per hour
        if len(analytics_list) > 1000:
            analytics_list = analytics_list[-1000:]
        
        cache.set(cache_key, analytics_list, 3600)  # 1 hour TTL


class ThemeCacheMiddleware(MiddlewareMixin):
    """
    Middleware to handle theme caching at the HTTP level.
    
    This middleware provides HTTP-level caching for theme CSS
    and other static theme resources.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cacheable_paths = [
            '/theming/api/v1/events/',
            '/theming/event/',
        ]
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check for cached responses."""
        
        # Only cache GET requests
        if request.method != 'GET':
            return None
        
        # Only cache specific paths
        if not any(request.path.startswith(path) for path in self.cacheable_paths):
            return None
        
        # Skip caching for authenticated users (for now)
        if request.user.is_authenticated:
            return None
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            
            # Check for cached response
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Serving cached response for {request.path}")
                
                # Update cache hit counter
                cache.set('theme_cache_hits', cache.get('theme_cache_hits', 0) + 1, 86400)
                
                return cached_response
            
            # Update total requests counter
            cache.set('theme_cache_total_requests', cache.get('theme_cache_total_requests', 0) + 1, 86400)
            
        except Exception as e:
            logger.error(f"Cache middleware error: {str(e)}")
        
        return None
    
    def process_response(self, request, response):
        """Cache successful responses."""
        
        # Only cache GET requests
        if request.method != 'GET':
            return response
        
        # Only cache specific paths
        if not any(request.path.startswith(path) for path in self.cacheable_paths):
            return response
        
        # Only cache successful responses
        if response.status_code != 200:
            return response
        
        # Skip caching for authenticated users
        if request.user.is_authenticated:
            return response
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            
            # Cache the response for 5 minutes
            cache.set(cache_key, response, 300)
            
            # Add cache headers
            response['Cache-Control'] = 'public, max-age=300'
            response['X-Cache-Status'] = 'MISS'
            
        except Exception as e:
            logger.error(f"Response caching error: {str(e)}")
        
        return response
    
    def _generate_cache_key(self, request):
        """Generate a cache key for the request."""
        import hashlib
        
        # Include path and query parameters
        cache_data = f"{request.path}?{request.GET.urlencode()}"
        
        # Create hash
        cache_hash = hashlib.md5(cache_data.encode()).hexdigest()
        
        return f"theme_http_cache_{cache_hash}"