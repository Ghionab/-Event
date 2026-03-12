"""
Decorators for staff portal access control
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def staff_required(view_func):
    """
    Decorator to restrict access to ADMIN, ORGANIZER, or STAFF roles
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role in ['admin', 'organizer', 'staff']:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'You do not have permission to access the staff portal.')
            return redirect('staff_login')
    return wrapper
