"""
Security middleware for the theming system.

Provides comprehensive security measures including:
- Content Security Policy headers
- Request validation and sanitization
- Rate limiting integration
- Security audit logging
"""

import logging
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from ..security import (
    api_security_manager, 
    security_validator, 
    audit_logger
)

logger = logging.getLogger(__name__)


class ThemeSecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware for theme-related requests.
    
    Applies security measures to all theme API endpoints and
    static theme resources.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.theme_paths = [
            '/api/v1/themes/',
            '/api/v1/events/',
            '/theming/',
            '/static/themes/'
        ]
    
    def process_request(self, request):
        """Process incoming requests for security validation."""
        # Check if this is a theme-related request
        if not any(request.path.startswith(path) for path in self.theme_paths):
            return None
        
        try:
            # Validate API requests
            if request.path.startswith('/api/'):
                validation_result = api_security_manager.validate_api_request(
                    request, 
                    self._get_operation_type(request)
                )
                
                if not validation_result['is_valid']:
                    # Log security violation
                    audit_logger.log_security_event(
                        'request_blocked',
                        request.user,
                        request,
                        errors=validation_result['errors'],
                        security_level=validation_result['security_level']
                    )
                    
                    return HttpResponse(
                        'Request blocked for security reasons',
                        status=403,
                        content_type='text/plain'
                    )
                
                # Store validation result for later use
                request.theme_security_validation = validation_result
        
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            # Fail securely - block request on security middleware failure
            return HttpResponse(
                'Security validation failed',
                status=500,
                content_type='text/plain'
            )
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing responses to add security headers."""
        # Check if this is a theme-related request
        if not any(request.path.startswith(path) for path in self.theme_paths):
            return response
        
        try:
            # Add Content Security Policy headers for theme CSS
            if hasattr(request, 'theme_css_content'):
                csp_headers = security_validator.generate_csp_headers(
                    request.theme_css_content
                )
                
                for header_name, header_value in csp_headers.items():
                    response[header_name] = header_value
            else:
                # Default CSP headers for theme endpoints
                response['Content-Security-Policy'] = (
                    "default-src 'self'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data:; "
                    "font-src 'self'; "
                    "object-src 'none'; "
                    "base-uri 'self';"
                )
            
            # Add additional security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Add cache control for theme resources
            if '/static/themes/' in request.path:
                response['Cache-Control'] = 'public, max-age=3600, must-revalidate'
            
        except Exception as e:
            logger.error(f"Security response processing error: {str(e)}")
        
        return response
    
    def _get_operation_type(self, request):
        """Determine the operation type for rate limiting."""
        if 'extract-colors' in request.path:
            return 'color_extraction'
        elif request.method == 'POST' and 'theme' in request.path:
            return 'theme_generation'
        else:
            return 'api_request'


class ThemeCSPMiddleware(MiddlewareMixin):
    """
    Specialized middleware for Content Security Policy enforcement
    on theme-generated content.
    """
    
    def process_response(self, request, response):
        """Add CSP headers specifically for theme content."""
        # Only apply to HTML responses with theme content
        if (response.get('Content-Type', '').startswith('text/html') and 
            hasattr(request, 'event_theme')):
            
            # Generate CSP based on theme content
            csp_directives = [
                "default-src 'self'",
                "style-src 'self' 'unsafe-inline'",  # Allow inline styles for themes
                "img-src 'self' data: blob:",  # Allow data URLs for images
                "font-src 'self'",
                "script-src 'self'",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'"
            ]
            
            response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        return response