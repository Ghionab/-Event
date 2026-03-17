from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Exempt CSRF for API endpoints while maintaining session security
    """
    def enforce_csrf(self, request):
        return  # Skip CSRF for API
