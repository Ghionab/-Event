"""
Admin-only security and system management views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .decorators import admin_required, security_admin_required
from events.models import Event
from registration.models import Registration, CheckIn
from organizers.models import OrganizerProfile, OrganizerTeamMember

User = get_user_model()

@security_admin_required
def admin_security_dashboard(request):
    """Main security dashboard for superusers"""
    context = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'superusers': User.objects.filter(is_superuser=True).count(),
        'recent_logins': User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).order_by('-last_login')[:10],
        'suspicious_activity': [],  # TODO: Implement activity logging
    }
    
    return render(request, 'admin/security_dashboard.html', context)

@security_admin_required
def admin_user_management(request):
    """User management for superusers"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filters
    role_filter = request.GET.get('role')
    if role_filter == 'staff':
        users = users.filter(is_staff=True)
    elif role_filter == 'superuser':
        users = users.filter(is_superuser=True)
    elif role_filter == 'organizer':
        users = users.filter(events__isnull=False).distinct()
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'search': search,
    }
    
    return render(request, 'admin/user_management.html', context)

@security_admin_required
def admin_user_detail(request, user_id):
    """Detailed user information for security review"""
    user = get_object_or_404(User, id=user_id)
    
    # User's events
    events = Event.objects.filter(organizer=user)
    
    # User's registrations
    registrations = Registration.objects.filter(user=user)
    
    # Team memberships
    team_memberships = OrganizerTeamMember.objects.filter(user=user)
    
    context = {
        'target_user': user,
        'events': events,
        'registrations': registrations,
        'team_memberships': team_memberships,
    }
    
    return render(request, 'admin/user_detail.html', context)

@security_admin_required
def admin_toggle_staff(request, user_id):
    """Toggle staff status for a user"""
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, 'You cannot modify your own staff status.')
        return redirect('system_admin:user_detail', user_id=user_id)
    
    user.is_staff = not user.is_staff
    user.save()
    
    status = 'granted' if user.is_staff else 'revoked'
    messages.success(request, f'Staff access {status} for {user.email}.')
    
    return redirect('system_admin:user_detail', user_id=user_id)

@security_admin_required
def admin_toggle_superuser(request, user_id):
    """Toggle superuser status for a user"""
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, 'You cannot modify your own superuser status.')
        return redirect('system_admin:user_detail', user_id=user_id)
    
    user.is_superuser = not user.is_superuser
    user.save()
    
    status = 'granted' if user.is_superuser else 'revoked'
    messages.success(request, f'Superuser access {status} for {user.email}.')
    
    return redirect('system_admin:user_detail', user_id=user_id)

@security_admin_required
def admin_system_logs(request):
    """View system security logs"""
    # TODO: Implement comprehensive logging
    logs = []  # Placeholder for security events
    
    context = {
        'logs': logs,
    }
    
    return render(request, 'admin/system_logs.html', context)

@security_admin_required
def admin_audit_events(request):
    """Audit trail for important events"""
    from advanced.models import AuditLog
    
    logs = AuditLog.objects.all().order_by('-timestamp')[:100]
    
    # Filters
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    user_filter = request.GET.get('user')
    if user_filter:
        logs = logs.filter(user__email__icontains=user_filter)
    
    context = {
        'logs': logs,
        'action_filter': action_filter,
        'user_filter': user_filter,
    }
    
    return render(request, 'admin/audit_events.html', context)

@admin_required
def admin_event_overview(request):
    """Overview of all events for admin monitoring"""
    events = Event.objects.all().order_by('-created_at')
    
    # Stats
    total_events = events.count()
    active_events = events.filter(
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).count()
    past_events = events.filter(end_date__lt=timezone.now().date()).count()
    upcoming_events = events.filter(start_date__gt=timezone.now().date()).count()
    
    # Recent events with issues
    problematic_events = events.filter(
        Q(end_date__lt=timezone.now().date(), registrations__status='pending') |
        Q(start_date__lte=timezone.now().date(), end_date__gte=timezone.now().date(), registrations__status='confirmed')
    ).distinct()
    
    context = {
        'events': events[:20],  # Show recent 20 events
        'total_events': total_events,
        'active_events': active_events,
        'past_events': past_events,
        'upcoming_events': upcoming_events,
        'problematic_events': problematic_events,
    }
    
    return render(request, 'admin/event_overview.html', context)

@admin_required
def admin_registration_monitoring(request):
    """Monitor all registrations across the system"""
    registrations = Registration.objects.all().order_by('-created_at')
    
    # Stats
    total_registrations = registrations.count()
    pending_registrations = registrations.filter(status='pending').count()
    confirmed_registrations = registrations.filter(status='confirmed').count()
    cancelled_registrations = registrations.filter(status='cancelled').count()
    
    # Recent suspicious activity (multiple registrations from same IP/email)
    # TODO: Implement IP tracking and suspicious activity detection
    
    context = {
        'registrations': registrations[:50],  # Show recent 50
        'total_registrations': total_registrations,
        'pending_registrations': pending_registrations,
        'confirmed_registrations': confirmed_registrations,
        'cancelled_registrations': cancelled_registrations,
    }
    
    return render(request, 'admin/registration_monitoring.html', context)
