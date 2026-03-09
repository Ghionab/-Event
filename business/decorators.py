from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def organizer_required(view_func):
    """
    Decorator that checks if user is logged in and is an organizer or staff member.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff or (hasattr(request.user, 'is_organizer') and request.user.is_organizer):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper
