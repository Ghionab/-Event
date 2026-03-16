from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse

from .decorators import coordinator_required, coordinator_event_required, get_coordinator_events, check_coordinator_event_access
from advanced.models import TeamMember, TeamRole
from events.models import Event, EventSession, Speaker, Sponsor, Room
from registration.models import Registration, RegistrationStatus
from communication.models import EmailTemplate, EmailLog


def coordinator_login(request):
    """Coordinator login view"""
    if request.user.is_authenticated:
        # Check if user is a coordinator for any event
        if TeamMember.objects.filter(user=request.user, role=TeamRole.COORDINATOR, is_active=True).exists():
            return redirect('coordinators:dashboard')
        else:
            messages.error(request, 'You are not assigned as a coordinator to any events.')
            return redirect('coordinators:coordinator_login')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Check if user is a coordinator for any event
            if TeamMember.objects.filter(user=user, role=TeamRole.COORDINATOR, is_active=True).exists():
                login(request, user)
                messages.success(request, 'Welcome to the Coordinator Portal!')
                return redirect('coordinators:dashboard')
            else:
                messages.error(request, 'You are not assigned as a coordinator to any events.')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'coordinators/login.html')


def coordinator_logout(request):
    """Coordinator logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('coordinators:coordinator_login')


@coordinator_required
def dashboard(request):
    """Coordinator dashboard with overview of assigned events"""
    events = get_coordinator_events(request.user)
    
    # Stats
    total_events = events.count()
    upcoming_events = events.filter(start_date__gte=timezone.now()).count()
    ongoing_events = events.filter(status='ongoing').count()
    
    # Registration stats (non-financial)
    total_registrations = Registration.objects.filter(event__in=events).count()
    confirmed_registrations = Registration.objects.filter(
        event__in=events, 
        status=RegistrationStatus.CONFIRMED
    ).count()
    checked_in_count = Registration.objects.filter(
        event__in=events, 
        status=RegistrationStatus.CHECKED_IN
    ).count()
    
    # Recent activity
    recent_registrations = Registration.objects.filter(
        event__in=events
    ).order_by('-created_at')[:5]
    
    # Upcoming sessions
    upcoming_sessions = EventSession.objects.filter(
        event__in=events,
        start_time__gte=timezone.now()
    ).order_by('start_time')[:5]
    
    context = {
        'events': events[:5],
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'ongoing_events': ongoing_events,
        'total_registrations': total_registrations,
        'confirmed_registrations': confirmed_registrations,
        'checked_in_count': checked_in_count,
        'recent_registrations': recent_registrations,
        'upcoming_sessions': upcoming_sessions,
    }
    return render(request, 'coordinators/dashboard.html', context)


@coordinator_required
def event_list(request):
    """List all events assigned to coordinator"""
    events = get_coordinator_events(request.user).order_by('-start_date')
    
    # Add registration counts to each event
    events_with_stats = []
    for event in events:
        events_with_stats.append({
            'event': event,
            'registration_count': Registration.objects.filter(event=event).count(),
            'confirmed_count': Registration.objects.filter(
                event=event, 
                status=RegistrationStatus.CONFIRMED
            ).count(),
            'session_count': EventSession.objects.filter(event=event).count(),
        })
    
    return render(request, 'coordinators/event_list.html', {'events_with_stats': events_with_stats})


@coordinator_required
@coordinator_event_required
def event_detail(request, event_id):
    """View event details"""
    event = get_object_or_404(Event, id=event_id)
    
    # Basic stats
    total_registrations = Registration.objects.filter(event=event).count()
    confirmed_registrations = Registration.objects.filter(
        event=event, 
        status=RegistrationStatus.CONFIRMED
    ).count()
    checked_in_count = Registration.objects.filter(
        event=event, 
        status=RegistrationStatus.CHECKED_IN
    ).count()
    
    # Event components
    sessions = EventSession.objects.filter(event=event).order_by('start_time')
    speakers = Speaker.objects.filter(event=event).order_by('name')
    sponsors = Sponsor.objects.filter(event=event).order_by('tier', 'company_name')
    rooms = Room.objects.filter(event=event).order_by('order', 'name')
    
    # Recent registrations (read-only)
    recent_registrations = Registration.objects.filter(
        event=event
    ).order_by('-created_at')[:10]
    
    context = {
        'event': event,
        'total_registrations': total_registrations,
        'confirmed_registrations': confirmed_registrations,
        'checked_in_count': checked_in_count,
        'sessions': sessions,
        'speakers': speakers,
        'sponsors': sponsors,
        'rooms': rooms,
        'recent_registrations': recent_registrations,
    }
    return render(request, 'coordinators/event_detail.html', context)


@coordinator_required
@coordinator_event_required
def event_edit(request, event_id):
    """Edit event details"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        # Handle event form submission
        event.title = request.POST.get('title', event.title)
        event.description = request.POST.get('description', event.description)
        event.venue_name = request.POST.get('venue_name', event.venue_name)
        event.address = request.POST.get('address', event.address)
        event.city = request.POST.get('city', event.city)
        event.country = request.POST.get('country', event.country)
        event.contact_email = request.POST.get('contact_email', event.contact_email)
        event.contact_phone = request.POST.get('contact_phone', event.contact_phone)
        
        # Handle dates
        if request.POST.get('start_date'):
            event.start_date = timezone.datetime.strptime(
                request.POST.get('start_date'), 
                '%Y-%m-%dT%H:%M'
            )
        if request.POST.get('end_date'):
            event.end_date = timezone.datetime.strptime(
                request.POST.get('end_date'), 
                '%Y-%m-%dT%H:%M'
            )
        
        event.save()
        messages.success(request, 'Event updated successfully!')
        return redirect('coordinators:event_detail', event_id=event.id)
    
    return render(request, 'coordinators/event_edit.html', {'event': event})


@coordinator_required
@coordinator_event_required
def session_list(request, event_id):
    """Manage event sessions"""
    event = get_object_or_404(Event, id=event_id)
    sessions = EventSession.objects.filter(event=event).order_by('start_time')
    
    return render(request, 'coordinators/session_list.html', {
        'event': event,
        'sessions': sessions
    })


@coordinator_required
@coordinator_event_required
def speaker_list(request, event_id):
    """Manage event speakers"""
    event = get_object_or_404(Event, id=event_id)
    speakers = Speaker.objects.filter(event=event).order_by('name')
    
    return render(request, 'coordinators/speaker_list.html', {
        'event': event,
        'speakers': speakers
    })


@coordinator_required
@coordinator_event_required
def sponsor_list(request, event_id):
    """Manage event sponsors"""
    event = get_object_or_404(Event, id=event_id)
    sponsors = Sponsor.objects.filter(event=event).order_by('tier', 'company_name')
    
    return render(request, 'coordinators/sponsor_list.html', {
        'event': event,
        'sponsors': sponsors
    })


@coordinator_required
@coordinator_event_required
def communications(request, event_id):
    """Event communications dashboard"""
    event = get_object_or_404(Event, id=event_id)
    
    # Get email templates and logs
    email_templates = EmailTemplate.objects.all()[:10]
    email_logs = EmailLog.objects.filter(event=event).order_by('-sent_at')[:20]
    
    return render(request, 'coordinators/communications.html', {
        'event': event,
        'email_templates': email_templates,
        'email_logs': email_logs
    })


@coordinator_required
def analytics(request):
    """Analytics dashboard for coordinator's events"""
    events = get_coordinator_events(request.user)
    
    # Calculate overall stats
    total_registrations = Registration.objects.filter(event__in=events).count()
    total_confirmed = Registration.objects.filter(
        event__in=events, 
        status=RegistrationStatus.CONFIRMED
    ).count()
    total_checked_in = Registration.objects.filter(
        event__in=events, 
        status=RegistrationStatus.CHECKED_IN
    ).count()
    
    # Event-specific stats
    event_stats = []
    for event in events:
        regs = Registration.objects.filter(event=event)
        confirmed = regs.filter(status=RegistrationStatus.CONFIRMED).count()
        checked_in = regs.filter(status=RegistrationStatus.CHECKED_IN).count()
        
        event_stats.append({
            'event': event,
            'total': regs.count(),
            'confirmed': confirmed,
            'checked_in': checked_in,
            'attendance_rate': (checked_in / regs.count() * 100) if regs.count() > 0 else 0
        })
    
    context = {
        'events': events,
        'total_registrations': total_registrations,
        'total_confirmed': total_confirmed,
        'total_checked_in': total_checked_in,
        'event_stats': event_stats,
    }
    return render(request, 'coordinators/analytics.html', context)
