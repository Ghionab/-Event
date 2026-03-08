"""
Custom middleware for participant portal
"""
from django.http import HttpResponse


class DisableCSRFMiddleware:
    """
    Middleware to disable CSRF for specific API endpoints only
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip CSRF check for registration API only
        if request.path == '/api/v1/register/' and request.method == 'POST':
            # Temporarily disable CSRF check
            request._dont_enforce_csrf_checks = True
        elif request.path.startswith('/api/v1/') and request.method in ['POST', 'PUT', 'DELETE']:
            # For other API endpoints, also disable CSRF
            request._dont_enforce_csrf_checks = True

        response = self.get_response(request)
        return response
