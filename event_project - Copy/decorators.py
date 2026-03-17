"""
Security decorators for separating admin and organizer permissions
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    """
    Decorator to require admin (superuser) access only.
    This is for sensitive admin-only functions.
    """
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Admin access required for this function.')
            return redirect('admin:login') if hasattr(request, 'user') else redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def organizer_or_admin_required(view_func):
    """
    Decorator to require either organizer access or admin access.
    This is for general organizer functions.
    """
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Admin users have access to everything
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Check if user is an organizer (has events)
        from events.models import Event
        if Event.objects.filter(organizer=request.user).exists():
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Organizer access required for this function.')
        return redirect('login')
    return _wrapped_view

def event_organizer_or_admin_required(view_func):
    """
    Decorator to require either:
    1. Admin access (staff user)
    2. Event organizer access (user owns the event)
    """
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Admin users have access to everything
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Check if user is the event organizer
        from events.models import Event
        event_id = kwargs.get('event_id') or kwargs.get('pk')
        
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
                if event.organizer == request.user:
                    return view_func(request, *args, **kwargs)
            except Event.DoesNotExist:
                pass
        
        messages.error(request, 'You must be the event organizer or admin to access this.')
        return redirect('home')
    return _wrapped_view

def security_admin_required(view_func):
    """
    Decorator specifically for security-related admin functions.
    Only superusers should access these.
    """
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Superuser access required for security functions.')
            return redirect('admin:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def can_manage_event(view_func):
    """
    Decorator to check if user can manage a specific event.
    Includes admin override and organizer ownership.
    """
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Admin users can manage all events
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Check event ownership
        from events.models import Event
        event_id = kwargs.get('event_id') or kwargs.get('pk')
        
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
                if event.organizer == request.user:
                    return view_func(request, *args, **kwargs)
            except Event.DoesNotExist:
                pass
        
        messages.error(request, 'You do not have permission to manage this event.')
        return redirect('events:list')
    return _wrapped_view

def can_view_registration(view_func):
    """
    Decorator to check if user can view a registration.
    Includes admin override, event organizer, and registration owner.
    """
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Admin users can view all registrations
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Check if user is the registration owner
        registration_id = kwargs.get('registration_id')
        if registration_id:
            try:
                from registration.models import Registration
                registration = Registration.objects.get(id=registration_id)
                if registration.user == request.user or registration.event.organizer == request.user:
                    return view_func(request, *args, **kwargs)
            except Registration.DoesNotExist:
                pass
        
        messages.error(request, 'You do not have permission to view this registration.')
        return redirect('home')
    return _wrapped_view
