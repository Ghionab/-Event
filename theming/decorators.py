"""
Security decorators for theme API endpoints.

This module provides decorators for adding security validation,
permission checks, and audit logging to API views.
"""

import functools
import logging
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from .security import api_security_manager, permission_manager, audit_logger

logger = logging.getLogger(__name__)


def secure_api_endpoint(operation_type='api_request', required_permission=None, 
                       audit_event_type=None, rate_limit_operation=None):
    """
    Decorator to add comprehensive security validation to API endpoints.
    
    Args:
        operation_type: Type of operation for rate limiting
        required_permission: Required permission for the operation
        audit_event_type: Type of audit event to log
        rate_limit_operation: Specific rate limit operation type
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # 1. Comprehensive security validation
                security_validation = api_security_manager.validate_api_request(
                    request, 
                    rate_limit_operation or operation_type
                )
                
                if not security_validation['is_valid']:
                    # Log security violation
                    if audit_event_type:
                        audit_logger.log_security_event(
                            f'{audit_event_type}_blocked',
                            request.user,
                            request,
                            errors=security_validation['errors'],
                            warnings=security_validation['warnings']
                        )
                    
                    return JsonResponse({
                        'error': 'Security validation failed',
                        'details': security_validation['errors'],
                        'warnings': security_validation['warnings']
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # 2. Permission check if required
                if required_permission:
                    # Get context objects
                    event = None
                    theme = None
                    
                    # Try to get event from URL parameters
                    event_id = kwargs.get('event_id')
                    if event_id:
                        try:
                            from events.models import Event
                            event = Event.objects.get(id=event_id)
                        except Event.DoesNotExist:
                            return JsonResponse({
                                'error': 'Event not found'
                            }, status=status.HTTP_404_NOT_FOUND)
                    
                    # Try to get theme from event
                    if event:
                        try:
                            from .models import EventTheme
                            theme = EventTheme.objects.get(event=event)
                        except EventTheme.DoesNotExist:
                            pass
                    
                    # Check permission
                    permission_result = permission_manager.check_permission(
                        request.user,
                        required_permission,
                        event,
                        theme
                    )
                    
                    if not permission_result['allowed']:
                        # Log permission denial
                        if audit_event_type:
                            audit_logger.log_security_event(
                                f'{audit_event_type}_permission_denied',
                                request.user,
                                request,
                                permission_result=permission_result
                            )
                        
                        return JsonResponse({
                            'error': 'Permission denied',
                            'reason': permission_result['reason'],
                            'required_roles': permission_result['required_roles']
                        }, status=status.HTTP_403_FORBIDDEN)
                
                # 3. Log successful access if audit event type is specified
                if audit_event_type:
                    audit_logger.log_security_event(
                        f'{audit_event_type}_accessed',
                        request.user,
                        request,
                        security_level=security_validation['security_level'],
                        **kwargs
                    )
                
                # 4. Add security info to request for use in view
                request.security_validation = security_validation
                
                # 5. Call the original view
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Security decorator error: {str(e)}")
                
                # Log security error
                if audit_event_type:
                    audit_logger.log_security_event(
                        f'{audit_event_type}_security_error',
                        request.user,
                        request,
                        error=str(e)
                    )
                
                return JsonResponse({
                    'error': 'Security validation error',
                    'message': 'An error occurred during security validation'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return wrapper
    return decorator


def secure_api_class(operation_type='api_request', required_permission=None, 
                    audit_event_type=None, rate_limit_operation=None):
    """
    Class decorator to add security validation to all methods of an API view class.
    
    Args:
        operation_type: Type of operation for rate limiting
        required_permission: Required permission for the operation
        audit_event_type: Type of audit event to log
        rate_limit_operation: Specific rate limit operation type
    """
    def decorator(cls):
        # Apply security decorator to common HTTP methods
        http_methods = ['get', 'post', 'put', 'patch', 'delete']
        
        for method_name in http_methods:
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                secured_method = secure_api_endpoint(
                    operation_type=operation_type,
                    required_permission=required_permission,
                    audit_event_type=audit_event_type,
                    rate_limit_operation=rate_limit_operation
                )(original_method)
                setattr(cls, method_name, secured_method)
        
        return cls
    return decorator


def validate_theme_colors(view_func):
    """
    Decorator to validate theme color values in request data.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                from .security import security_validator
                
                # Get color fields from request data
                color_fields = [
                    'primary_color', 'secondary_color', 'accent_color',
                    'neutral_light', 'neutral_dark'
                ]
                
                validation_errors = []
                
                for field in color_fields:
                    if field in request.data:
                        color_value = request.data[field]
                        if not security_validator.validate_color_value(color_value):
                            validation_errors.append(f'Invalid color value for {field}: {color_value}')
                
                if validation_errors:
                    return JsonResponse({
                        'error': 'Color validation failed',
                        'details': validation_errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Color validation error: {str(e)}")
                return JsonResponse({
                    'error': 'Color validation error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def validate_css_content(view_func):
    """
    Decorator to validate CSS content in request data.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                from .security import security_validator
                
                css_content = request.data.get('css_content')
                if css_content:
                    validation_result = security_validator.validate_css_content(css_content)
                    
                    if not validation_result['is_valid']:
                        return JsonResponse({
                            'error': 'CSS validation failed',
                            'details': validation_result['errors'],
                            'warnings': validation_result['warnings']
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Replace with sanitized CSS
                    request.data['css_content'] = validation_result['sanitized_css']
                
            except Exception as e:
                logger.error(f"CSS validation error: {str(e)}")
                return JsonResponse({
                    'error': 'CSS validation error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def log_api_access(event_type):
    """
    Decorator to log API access for audit purposes.
    
    Args:
        event_type: Type of event to log
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Log the access attempt
                audit_logger.log_security_event(
                    f'{event_type}_attempt',
                    request.user,
                    request,
                    **kwargs
                )
                
                # Call the original view
                response = view_func(request, *args, **kwargs)
                
                # Log the result
                audit_logger.log_security_event(
                    f'{event_type}_completed',
                    request.user,
                    request,
                    status_code=response.status_code if hasattr(response, 'status_code') else 200,
                    **kwargs
                )
                
                return response
                
            except Exception as e:
                # Log the error
                audit_logger.log_security_event(
                    f'{event_type}_error',
                    request.user,
                    request,
                    error=str(e),
                    **kwargs
                )
                raise
        
        return wrapper
    return decorator


def require_https(view_func):
    """
    Decorator to require HTTPS for sensitive operations.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.is_secure() and not settings.DEBUG:
            return JsonResponse({
                'error': 'HTTPS required',
                'message': 'This operation requires a secure connection'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def validate_file_upload(allowed_types=None, max_size=None):
    """
    Decorator to validate file uploads.
    
    Args:
        allowed_types: List of allowed file types
        max_size: Maximum file size in bytes
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST' and request.FILES:
                try:
                    from .security import image_processor
                    
                    for field_name, uploaded_file in request.FILES.items():
                        # Validate file size
                        if max_size and uploaded_file.size > max_size:
                            return JsonResponse({
                                'error': f'File too large: {uploaded_file.name}',
                                'max_size': max_size
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Validate file type
                        if allowed_types:
                            file_ext = uploaded_file.name.split('.')[-1].upper()
                            if file_ext not in allowed_types:
                                return JsonResponse({
                                    'error': f'File type not allowed: {file_ext}',
                                    'allowed_types': allowed_types
                                }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Additional security validation would go here
                        # (This would require saving the file temporarily)
                
                except Exception as e:
                    logger.error(f"File upload validation error: {str(e)}")
                    return JsonResponse({
                        'error': 'File validation error'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Convenience decorators for common use cases

def secure_theme_api(required_permission=None):
    """Convenience decorator for theme API endpoints."""
    return secure_api_endpoint(
        operation_type='theme_api',
        required_permission=required_permission,
        audit_event_type='theme_api',
        rate_limit_operation='api_requests'
    )


def secure_color_extraction():
    """Convenience decorator for color extraction endpoints."""
    return secure_api_endpoint(
        operation_type='color_extraction',
        required_permission='extract_colors',
        audit_event_type='color_extraction',
        rate_limit_operation='color_extraction'
    )


def secure_theme_generation():
    """Convenience decorator for theme generation endpoints."""
    return secure_api_endpoint(
        operation_type='theme_generation',
        required_permission='create_theme',
        audit_event_type='theme_generation',
        rate_limit_operation='theme_generation'
    )


def secure_admin_api():
    """Convenience decorator for admin-only endpoints."""
    return secure_api_endpoint(
        operation_type='admin_api',
        required_permission='system_admin',
        audit_event_type='admin_api',
        rate_limit_operation='api_requests'
    )