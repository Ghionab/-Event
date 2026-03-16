from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from advanced.models import TeamMember, TeamRole
from events.models import Event


def coordinator_required(view_func):
    """Decorator to ensure user has coordinator role for at least one event"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not TeamMember.objects.filter(
            user=request.user, 
            role=TeamRole.COORDINATOR, 
            is_active=True
        ).exists():
            messages.error(request, 'You do not have coordinator privileges.')
            return redirect('coordinators:coordinator_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_coordinator_events(user):
    """Get all events where user is a coordinator"""
    return Event.objects.filter(
        team_members__user=user,
        team_members__role=TeamRole.COORDINATOR,
        team_members__is_active=True
    ).distinct()


def check_coordinator_event_access(user, event_id):
    """Check if coordinator has access to specific event"""
    return TeamMember.objects.filter(
        user=user,
        event_id=event_id,
        role=TeamRole.COORDINATOR,
        is_active=True
    ).exists()


def coordinator_event_required(view_func):
    """Decorator to ensure coordinator has access to specific event"""
    def wrapper(request, event_id, *args, **kwargs):
        if not check_coordinator_event_access(request.user, event_id):
            messages.error(request, 'You do not have access to this event.')
            return redirect('coordinators:event_list')
        return view_func(request, event_id, *args, **kwargs)
    return wrapper
