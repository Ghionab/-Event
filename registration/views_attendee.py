"""
Attendee-specific views for enhanced attendee experience
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from datetime import datetime, timedelta

from .models import (
    Registration, RegistrationStatus, AttendeePreference,
    SessionAttendance, AttendeeMessage, Badge
)
from events.models import Event, EventSession, Speaker
from users.models import User


# =============================================================================
# PRIORITY 1: Core Attendee Dashboard
# =============================================================================

@login_required
def attendee_dashboard(request):
    """Enhanced attendee dashboard with comprehensive overview"""
    user = request.user
    now = timezone.now()
    
    # Get all registrations
    all_registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).select_related('event', 'ticket_type').order_by('-created_at')
    
    # Separate upcoming and past events
    upcoming_registrations_qs = all_registrations.filter(
        event__start_date__gte=now,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    )
    upcoming_registrations = upcoming_registrations_qs[:5]
    
    past_registrations_qs = all_registrations.filter(
        event__start_date__lt=now
    )
    past_registrations = past_registrations_qs[:5]
    
    # Get unread messages count
    unread_messages = AttendeeMessage.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    # Get saved sessions count
    saved_sessions_count = 0
    for reg in upcoming_registrations:
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            saved_sessions_count += len(prefs.saved_sessions)
    
    # Quick stats
    stats = {
        'total_events': all_registrations.count(),
        'upcoming_events': upcoming_registrations_qs.count(),
        'past_events': past_registrations_qs.filter(status=RegistrationStatus.CHECKED_IN).count(),
        'unread_messages': unread_messages,
        'saved_sessions': saved_sessions_count,
    }

    
    context = {
        'upcoming_registrations': upcoming_registrations,
        'past_registrations': past_registrations,
        'stats': stats,
    }
    
    return render(request, 'participant/attendee_dashboard.html', context)


@login_required
def my_registrations_enhanced(request):
    """Enhanced registration list with filtering and search"""
    user = request.user
    now = timezone.now()
    
    # Get all registrations
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).select_related('event', 'ticket_type').order_by('-created_at')
    
    # Apply filters
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'upcoming':
        registrations = registrations.filter(event__start_date__gte=now)
    elif filter_type == 'past':
        registrations = registrations.filter(event__start_date__lt=now)
    elif filter_type == 'cancelled':
        registrations = registrations.filter(status=RegistrationStatus.CANCELLED)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        registrations = registrations.filter(
            models.Q(event__title__icontains=search_query) |
            models.Q(registration_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(registrations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    
    return render(request, 'participant/my_registrations_enhanced.html', context)


@login_required
def registration_detail_enhanced(request, registration_id):
    """Enhanced registration detail view"""
    registration = get_object_or_404(
        Registration.objects.select_related('event', 'ticket_type'),
        id=registration_id
    )
    
    # Check permission
    if registration.user != request.user and registration.attendee_email != request.user.email:
        messages.error(request, 'You do not have permission to view this registration.')
        return redirect('registration:attendee_dashboard')
    
    # Get event sessions
    sessions = registration.event.sessions.all().order_by('start_time')
    
    # Get speakers
    speakers = registration.event.speakers.filter(is_confirmed=True)
    
    # Get badge
    badge = getattr(registration, 'badge', None)
    if not badge:
        # Create badge if doesn't exist
        from .models import Badge
        badge = Badge.objects.create(
            registration=registration,
            name=registration.attendee_name,
            badge_type='vip' if registration.ticket_type and registration.ticket_type.ticket_category == 'vip' else 'standard',
            qr_code_data=f"REG:{registration.qr_code}",
        )
    
    # Get QR code image
    qr_code_image = registration.generate_qr_code_image()
    
    # Get attendee preferences
    preferences = AttendeePreference.objects.filter(
        user=request.user,
        event=registration.event
    ).first()
    
    # Get saved sessions
    saved_session_ids = preferences.saved_sessions if preferences else []
    
    context = {
        'registration': registration,
        'sessions': sessions,
        'speakers': speakers,
        'badge': badge,
        'qr_code_image': qr_code_image,
        'preferences': preferences,
        'saved_session_ids': saved_session_ids,
    }
    
    return render(request, 'participant/registration_detail_enhanced.html', context)


@login_required
def cancel_registration_enhanced(request, registration_id):
    """Cancel a registration with confirmation"""
    registration = get_object_or_404(Registration, id=registration_id)
    
    # Check permission
    if registration.user != request.user and registration.attendee_email != request.user.email:
        messages.error(request, 'You do not have permission to cancel this registration.')
        return redirect('registration:attendee_dashboard')
    
    # Check if event has started
    if registration.event.start_date < timezone.now():
        messages.error(request, 'Cannot cancel registration for events that have already started.')
        return redirect('registration:registration_detail_enhanced', registration_id=registration.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        registration.cancel(reason=reason)
        messages.success(request, 'Registration cancelled successfully.')
        return redirect('registration:my_registrations_enhanced')
    
    context = {
        'registration': registration,
    }
    
    return render(request, 'participant/cancel_registration.html', context)


@login_required
def download_ticket(request, registration_id):
    """Download ticket as PDF"""
    registration = get_object_or_404(Registration, id=registration_id)
    
    # Check permission
    if registration.user != request.user and registration.attendee_email != request.user.email:
        messages.error(request, 'You do not have permission to download this ticket.')
        return redirect('registration:attendee_dashboard')
    
    # Generate QR code
    qr_code_image = registration.generate_qr_code_image()
    
    context = {
        'registration': registration,
        'qr_code_image': qr_code_image,
    }
    
    # Render ticket template
    return render(request, 'participant/ticket_download.html', context)


# =============================================================================
# PRIORITY 2: Enhanced Event Discovery
# =============================================================================

def event_search(request):
    """Advanced event search with filters"""
    now = timezone.now()
    
    # Base queryset - only published and future events
    events = Event.objects.filter(
        status='published',
        start_date__gte=now
    ).order_by('start_date')
    
    # Event type filter
    event_type = request.GET.get('type')
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        events = events.filter(start_date__gte=date_from)
    if date_to:
        events = events.filter(start_date__lte=date_to)
    
    # Price range filter
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min or price_max:
        # Filter by ticket prices
        from .models import TicketType
        ticket_events = TicketType.objects.filter(is_active=True)
        if price_min:
            ticket_events = ticket_events.filter(price__gte=price_min)
        if price_max:
            ticket_events = ticket_events.filter(price__lte=price_max)
        event_ids = ticket_events.values_list('event_id', flat=True).distinct()
        events = events.filter(id__in=event_ids)
    
    # Location filter
    location = request.GET.get('location')
    if location:
        events = events.filter(
            models.Q(city__icontains=location) |
            models.Q(venue_name__icontains=location)
        )
    
    # Search query
    search_query = request.GET.get('search', '')
    if search_query:
        events = events.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    # Sort
    sort_by = request.GET.get('sort', 'date')
    if sort_by == 'date':
        events = events.order_by('start_date')
    elif sort_by == 'price_low':
        # This would need a more complex query
        pass
    elif sort_by == 'popularity':
        events = events.annotate(
            reg_count=models.Count('registrations')
        ).order_by('-reg_count')
    
    # Pagination
    paginator = Paginator(events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'event_type': event_type,
        'location': location,
        'sort_by': sort_by,
    }
    
    return render(request, 'participant/event_search.html', context)


def event_detail_enhanced(request, event_id):
    """Enhanced event detail page"""
    event = get_object_or_404(Event, id=event_id, status='published')
    
    # Get sessions preview
    sessions = event.sessions.all().order_by('start_time')[:5]
    
    # Get featured speakers
    speakers = event.speakers.filter(is_confirmed=True, is_featured=True)[:4]
    
    # Get attendee count
    attendee_count = Registration.objects.filter(
        event=event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).count()
    
    # Get ticket types
    ticket_types = event.ticket_types.filter(is_active=True)
    
    # Check if user is registered
    is_registered = False
    user_registration = None
    if request.user.is_authenticated:
        user_registration = Registration.objects.filter(
            models.Q(user=request.user) | models.Q(attendee_email=request.user.email)
        ).filter(
            event=event,
            status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
        ).first()
        is_registered = user_registration is not None
    
    # Check if event is saved
    is_saved = False
    if request.user.is_authenticated:
        # Check in user's saved events (would need a SavedEvent model)
        pass
    
    # Get similar events
    similar_events = Event.objects.filter(
        status='published',
        start_date__gte=timezone.now()
    ).exclude(id=event.id).order_by('start_date')[:3]
    
    context = {
        'event': event,
        'sessions': sessions,
        'speakers': speakers,
        'attendee_count': attendee_count,
        'ticket_types': ticket_types,
        'is_registered': is_registered,
        'user_registration': user_registration,
        'is_saved': is_saved,
        'similar_events': similar_events,
    }
    
    return render(request, 'participant/event_detail_enhanced.html', context)


@login_required
def save_event(request, event_id):
    """Save/unsave an event to favorites"""
    event = get_object_or_404(Event, id=event_id)
    
    # This would use a SavedEvent model (to be created)
    # For now, store in user's notification_preferences JSON field
    user = request.user
    saved_events = user.notification_preferences.get('saved_events', [])
    
    if event_id in saved_events:
        saved_events.remove(event_id)
        messages.success(request, f'Removed "{event.title}" from saved events.')
    else:
        saved_events.append(event_id)
        messages.success(request, f'Saved "{event.title}" to your favorites.')
    
    user.notification_preferences['saved_events'] = saved_events
    user.save()
    
    return redirect('registration:event_detail_enhanced', event_id=event_id)


@login_required
def saved_events(request):
    """View all saved events"""
    user = request.user
    saved_event_ids = user.notification_preferences.get('saved_events', [])
    
    events = Event.objects.filter(
        id__in=saved_event_ids,
        status='published'
    ).order_by('start_date')
    
    context = {
        'events': events,
    }
    
    return render(request, 'participant/saved_events.html', context)



# =============================================================================
# PRIORITY 3: Personal Schedule & Session Management
# =============================================================================

@login_required
def my_schedule(request):
    """View personal schedule across all events"""
    user = request.user
    now = timezone.now()
    
    # Get upcoming registrations
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email),
        event__start_date__gte=now,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')
    
    # Get saved sessions for each event
    schedule_items = []
    for reg in registrations:
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions,
                event=reg.event
            ).order_by('start_time')
            for session in sessions:
                schedule_items.append({
                    'registration': reg,
                    'session': session,
                    'event': reg.event,
                })
    
    # Sort by start time
    schedule_items.sort(key=lambda x: x['session'].start_time)
    
    # Detect conflicts
    conflicts = []
    for i, item in enumerate(schedule_items):
        for j, other in enumerate(schedule_items[i+1:], i+1):
            if item['session'].start_time < other['session'].end_time and \
               item['session'].end_time > other['session'].start_time:
                conflicts.append((i, j))
    
    context = {
        'schedule_items': schedule_items,
        'conflicts': conflicts,
    }
    
    return render(request, 'participant/my_schedule.html', context)


@login_required
def event_schedule(request, event_id):
    """View schedule for a specific event"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    
    # Check if user is registered
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).filter(
        event=event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        messages.error(request, 'You must be registered for this event to view the schedule.')
        return redirect('registration:event_detail_enhanced', event_id=event_id)
    
    # Get all sessions
    sessions = event.sessions.all().order_by('start_time')
    
    # Get user's saved sessions
    prefs = AttendeePreference.objects.filter(user=user, event=event).first()
    saved_session_ids = prefs.saved_sessions if prefs else []
    
    # Get tracks
    tracks = event.tracks.all()
    
    # Group sessions by day
    sessions_by_day = {}
    for session in sessions:
        day = session.start_time.date()
        if day not in sessions_by_day:
            sessions_by_day[day] = []
        sessions_by_day[day].append(session)
    
    context = {
        'event': event,
        'registration': registration,
        'sessions': sessions,
        'sessions_by_day': sessions_by_day,
        'tracks': tracks,
        'saved_session_ids': saved_session_ids,
    }
    
    return render(request, 'participant/event_schedule.html', context)


@login_required
def save_session(request, session_id):
    """Save/unsave a session to personal schedule"""
    session = get_object_or_404(EventSession, id=session_id)
    user = request.user
    
    # Check if user is registered for the event
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).filter(
        event=session.event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        return JsonResponse({'success': False, 'message': 'You must be registered for this event.'})
    
    # Get or create preferences
    prefs, created = AttendeePreference.objects.get_or_create(
        user=user,
        event=session.event,
        defaults={'saved_sessions': []}
    )
    
    # Toggle session
    saved_sessions = prefs.saved_sessions or []
    if session_id in saved_sessions:
        saved_sessions.remove(session_id)
        action = 'removed'
    else:
        saved_sessions.append(session_id)
        action = 'added'
    
    prefs.saved_sessions = saved_sessions
    prefs.save()
    
    return JsonResponse({
        'success': True,
        'action': action,
        'session_id': session_id
    })


@login_required
def session_feedback_enhanced(request, session_id):
    """Submit enhanced feedback for a session"""
    session = get_object_or_404(EventSession, id=session_id)
    user = request.user
    
    # Get user's registration
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).filter(
        event=session.event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        messages.error(request, 'You must be registered for this event.')
        return redirect('registration:event_detail_enhanced', event_id=session.event.id)
    
    # Get or create attendance
    attendance, created = SessionAttendance.objects.get_or_create(
        registration=registration,
        session=session
    )
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        feedback = request.POST.get('feedback', '')
        
        if rating:
            attendance.rating = int(rating)
            attendance.feedback = feedback
            attendance.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('registration:event_schedule', event_id=session.event.id)
    
    context = {
        'session': session,
        'attendance': attendance,
        'registration': registration,
    }
    
    return render(request, 'participant/session_feedback.html', context)


# =============================================================================
# PRIORITY 4: Networking & Communication
# =============================================================================

@login_required
def networking_hub(request):
    """Networking hub - overview of networking features"""
    user = request.user
    
    # Get user's upcoming events
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email),
        event__start_date__gte=timezone.now(),
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')
    
    # Get recent messages
    recent_messages = AttendeeMessage.objects.filter(
        recipient=user
    ).select_related('sender', 'event').order_by('-created_at')[:5]
    
    # Get unread count
    unread_count = AttendeeMessage.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    context = {
        'registrations': registrations,
        'recent_messages': recent_messages,
        'unread_count': unread_count,
    }
    
    return render(request, 'participant/networking_hub.html', context)


@login_required
def browse_attendees(request):
    """Browse other attendees for networking"""
    user = request.user
    event_id = request.GET.get('event')
    
    # Get attendees
    if event_id:
        event = get_object_or_404(Event, id=event_id)
        # Get all confirmed registrations for this event
        registrations = Registration.objects.filter(
            event=event,
            status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
        ).exclude(
            models.Q(user=user) | models.Q(attendee_email=user.email)
        ).select_related('user')
        
        # Get users with networking enabled
        attendees = []
        for reg in registrations:
            if reg.user:
                prefs = AttendeePreference.objects.filter(
                    user=reg.user,
                    event=event,
                    networking_enabled=True
                ).first()
                if prefs:
                    attendees.append({
                        'user': reg.user,
                        'registration': reg,
                        'preferences': prefs,
                    })
    else:
        attendees = []
    
    # Get user's events for filter
    user_events = Event.objects.filter(
        registrations__user=user,
        start_date__gte=timezone.now()
    ).distinct()
    
    context = {
        'attendees': attendees,
        'selected_event_id': event_id,
        'user_events': user_events,
    }
    
    return render(request, 'participant/browse_attendees.html', context)


@login_required
def attendee_profile(request, user_id):
    """View another attendee's public profile"""
    profile_user = get_object_or_404(User, id=user_id)
    
    # Get common events
    current_user_events = set(Event.objects.filter(
        registrations__user=request.user
    ).values_list('id', flat=True))
    
    profile_user_events = Event.objects.filter(
        registrations__user=profile_user,
        id__in=current_user_events
    )
    
    # Get preferences for common events
    preferences = AttendeePreference.objects.filter(
        user=profile_user,
        event__in=profile_user_events,
        networking_enabled=True
    )
    
    context = {
        'profile_user': profile_user,
        'common_events': profile_user_events,
        'preferences': preferences,
    }
    
    return render(request, 'participant/attendee_profile.html', context)


@login_required
def send_connection_request(request, user_id):
    """Send a connection request / message to another attendee"""
    recipient = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        message_text = request.POST.get('message', '')
        
        event = None
        if event_id:
            event = get_object_or_404(Event, id=event_id)
        
        # Create message
        AttendeeMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            event=event,
            subject='Connection Request',
            message=message_text
        )
        
        messages.success(request, f'Connection request sent to {recipient.email}')
        return redirect('registration:networking_hub')
    
    # Get common events
    common_events = Event.objects.filter(
        registrations__user=request.user
    ).filter(
        registrations__user=recipient
    ).distinct()
    
    context = {
        'recipient': recipient,
        'common_events': common_events,
    }
    
    return render(request, 'participant/send_connection_request.html', context)


@login_required
def messages_enhanced(request):
    """Enhanced messaging interface"""
    user = request.user
    
    # Get all messages
    received = AttendeeMessage.objects.filter(
        recipient=user
    ).select_related('sender', 'event').order_by('-created_at')
    
    sent = AttendeeMessage.objects.filter(
        sender=user
    ).select_related('recipient', 'event').order_by('-created_at')
    
    # Filter
    filter_type = request.GET.get('filter', 'received')
    if filter_type == 'sent':
        messages_list = sent
    else:
        messages_list = received
    
    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Unread count
    unread_count = received.filter(is_read=False).count()
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'unread_count': unread_count,
    }
    
    return render(request, 'participant/messages_enhanced.html', context)


@login_required
def send_message_enhanced(request, recipient_id):
    """Send a message to another attendee"""
    recipient = get_object_or_404(User, id=recipient_id)
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        message_text = request.POST.get('message', '')
        event_id = request.POST.get('event_id')
        
        event = None
        if event_id:
            event = get_object_or_404(Event, id=event_id)
        
        AttendeeMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            event=event,
            subject=subject,
            message=message_text
        )
        
        messages.success(request, f'Message sent to {recipient.email}')
        return redirect('registration:messages_enhanced')
    
    # Get common events
    common_events = Event.objects.filter(
        registrations__user=request.user
    ).filter(
        registrations__user=recipient
    ).distinct()
    
    context = {
        'recipient': recipient,
        'common_events': common_events,
    }
    
    return render(request, 'participant/send_message.html', context)


@login_required
def mark_message_read_enhanced(request, message_id):
    """Mark a message as read"""
    message = get_object_or_404(AttendeeMessage, id=message_id, recipient=request.user)
    
    if not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
    
    return redirect('registration:messages_enhanced')


# =============================================================================
# PRIORITY 5: Preferences & Settings
# =============================================================================

@login_required
def preferences_enhanced(request, event_id):
    """Enhanced preferences management for an event"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    
    # Check if user is registered
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).filter(
        event=event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        messages.error(request, 'You must be registered for this event.')
        return redirect('registration:event_detail_enhanced', event_id=event_id)
    
    # Get or create preferences
    prefs, created = AttendeePreference.objects.get_or_create(
        user=user,
        event=event,
        defaults={}
    )
    
    if request.method == 'POST':
        # Update preferences
        prefs.interested_topics = request.POST.getlist('interested_topics', [])
        prefs.preferred_tracks = request.POST.getlist('preferred_tracks', [])
        prefs.dietary_requirements = request.POST.getlist('dietary_requirements', [])
        prefs.dietary_notes = request.POST.get('dietary_notes', '')
        prefs.accessibility_needs = request.POST.getlist('accessibility_needs', [])
        prefs.accessibility_notes = request.POST.get('accessibility_notes', '')
        prefs.networking_enabled = 'networking_enabled' in request.POST
        prefs.networking_bio = request.POST.get('networking_bio', '')
        prefs.linkedin_url = request.POST.get('linkedin_url', '')
        prefs.twitter_handle = request.POST.get('twitter_handle', '')
        prefs.email_notifications = 'email_notifications' in request.POST
        prefs.sms_notifications = 'sms_notifications' in request.POST
        prefs.save()
        
        messages.success(request, 'Preferences saved successfully!')
        return redirect('registration:registration_detail_enhanced', registration_id=registration.id)
    
    # Get tracks for selection
    tracks = event.tracks.all()
    
    context = {
        'event': event,
        'registration': registration,
        'preferences': prefs,
        'tracks': tracks,
    }
    
    return render(request, 'participant/preferences.html', context)


@login_required
def account_settings(request):
    """Account settings page"""
    user = request.user
    
    if request.method == 'POST':
        # Update user profile
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.company = request.POST.get('company', '')
        user.job_title = request.POST.get('job_title', '')
        user.bio = request.POST.get('bio', '')
        user.linkedin_url = request.POST.get('linkedin_url', '')
        user.twitter_handle = request.POST.get('twitter_handle', '')
        user.website = request.POST.get('website', '')
        
        # Handle profile image upload
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        
        user.save()
        messages.success(request, 'Settings saved successfully!')
        return redirect('registration:account_settings')
    
    context = {
        'user': user,
    }
    
    return render(request, 'participant/account_settings.html', context)


# =============================================================================
# PRIORITY 6: Check-In & Badge Management
# =============================================================================

@login_required
def my_tickets(request):
    """Display all purchased tickets including upcoming and past events"""
    user = request.user
    now = timezone.now()

    # Get all confirmed/checked-in registrations for this user
    all_registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email),
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event', 'ticket_type').order_by('event__start_date')

    # Separate into upcoming and past
    upcoming_registrations = all_registrations.filter(event__start_date__gte=now)
    past_registrations = all_registrations.filter(event__start_date__lt=now)

    def create_tickets_list(registrations):
        tickets = []
        for reg in registrations:
            try:
                qr_image = reg.generate_qr_code_image()
            except Exception:
                qr_image = None
            tickets.append({
                'registration': reg,
                'qr_image': qr_image,
            })
        return tickets

    upcoming_tickets = create_tickets_list(upcoming_registrations)
    past_tickets = create_tickets_list(past_registrations)

    context = {
        'upcoming_tickets': upcoming_tickets,
        'past_tickets': past_tickets,
        'has_any_tickets': all_registrations.exists(),
    }
    return render(request, 'participant/my_tickets.html', context)


@login_required
def digital_badge(request, registration_id):
    """Display digital badge with social sharing options"""
    registration = get_object_or_404(Registration, id=registration_id)

    if registration.user != request.user and registration.attendee_email != request.user.email:
        messages.error(request, 'You do not have permission to view this badge.')
        return redirect('attendee:dashboard')

    badge = getattr(registration, 'badge', None)
    if not badge:
        badge = Badge.objects.create(
            registration=registration,
            name=registration.attendee_name,
            badge_type='vip' if registration.ticket_type and registration.ticket_type.ticket_category == 'vip' else 'standard',
            qr_code_data=f"BADGE:{registration.qr_code}",
        )

    try:
        qr_image = badge.generate_qr_code()
    except Exception:
        qr_image = None

    context = {
        'registration': registration,
        'badge': badge,
        'qr_image': qr_image,
    }
    return render(request, 'participant/digital_badge.html', context)


# =============================================================================
# PRIORITY 7: Post-Event Experience
# =============================================================================

@login_required
def certificates_list(request):
    """List all events where attendee has checked-in status"""
    user = request.user

    checked_in_registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email),
        status=RegistrationStatus.CHECKED_IN
    ).select_related('event').order_by('-event__start_date')

    context = {
        'registrations': checked_in_registrations,
    }
    return render(request, 'participant/certificates.html', context)


@login_required
def download_certificate(request, registration_id):
    """Generate and download PDF certificate"""
    registration = get_object_or_404(Registration, id=registration_id)

    if registration.user != request.user and registration.attendee_email != request.user.email:
        messages.error(request, 'You do not have permission to download this certificate.')
        return redirect('attendee:certificates')

    if registration.status != RegistrationStatus.CHECKED_IN:
        messages.error(request, 'Certificate is only available for events you have checked in to.')
        return redirect('attendee:certificates')

    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate_{registration.registration_number}.pdf"'

        c = canvas.Canvas(response, pagesize=landscape(A4))
        width, height = landscape(A4)

        # Background
        c.setFillColor(HexColor('#f8f9fa'))
        c.rect(0, 0, width, height, fill=1)

        # Border
        c.setStrokeColor(HexColor('#4f46e5'))
        c.setLineWidth(4)
        c.rect(30, 30, width - 60, height - 60)
        c.setLineWidth(1)
        c.rect(40, 40, width - 80, height - 80)

        # Title
        c.setFillColor(HexColor('#4f46e5'))
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(width / 2, height - 120, "Certificate of Attendance")

        # Decorative line
        c.setStrokeColor(HexColor('#a78bfa'))
        c.setLineWidth(2)
        c.line(width / 2 - 150, height - 135, width / 2 + 150, height - 135)

        # Body text
        c.setFillColor(HexColor('#374151'))
        c.setFont("Helvetica", 16)
        c.drawCentredString(width / 2, height - 180, "This is to certify that")

        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(HexColor('#1f2937'))
        c.drawCentredString(width / 2, height - 220, registration.attendee_name)

        c.setFont("Helvetica", 16)
        c.setFillColor(HexColor('#374151'))
        c.drawCentredString(width / 2, height - 260, "has successfully attended")

        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(HexColor('#4f46e5'))
        c.drawCentredString(width / 2, height - 300, registration.event.title)

        c.setFont("Helvetica", 14)
        c.setFillColor(HexColor('#6b7280'))
        date_str = registration.event.start_date.strftime('%B %d, %Y')
        venue = registration.event.venue_name or 'Virtual Event'
        c.drawCentredString(width / 2, height - 335, f"held on {date_str} at {venue}")

        # Registration number
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor('#9ca3af'))
        c.drawCentredString(width / 2, 70, f"Certificate ID: {registration.registration_number}")

        c.save()
        return response

    except ImportError:
        messages.error(request, 'PDF generation is not available. Please install reportlab.')
        return redirect('attendee:certificates')


@login_required
def event_materials(request, event_id):
    """Access session materials for a registered event"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).filter(
        event=event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()

    if not registration:
        messages.error(request, 'You must be registered for this event to access materials.')
        return redirect('attendee:event_detail', event_id=event_id)

    sessions_with_materials = event.sessions.filter(
        models.Q(slides__isnull=False) |
        models.Q(recording_url__gt='') |
        models.Q(resources__isnull=False)
    ).exclude(
        slides='', recording_url='', resources=[]
    ).order_by('start_time')

    context = {
        'event': event,
        'registration': registration,
        'sessions': sessions_with_materials,
    }
    return render(request, 'participant/event_materials.html', context)


@login_required
def event_feedback(request, event_id):
    """Submit overall event feedback"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).filter(
        event=event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()

    if not registration:
        messages.error(request, 'You must be registered for this event to submit feedback.')
        return redirect('attendee:event_detail', event_id=event_id)

    if request.method == 'POST':
        overall_rating = request.POST.get('overall_rating')
        feedback_text = request.POST.get('feedback', '')

        registration.custom_fields['event_feedback'] = {
            'rating': int(overall_rating) if overall_rating else None,
            'feedback': feedback_text,
            'submitted_at': timezone.now().isoformat(),
        }
        registration.save()
        messages.success(request, 'Thank you for your feedback!')
        return redirect('attendee:registration_detail', registration_id=registration.id)

    existing_feedback = registration.custom_fields.get('event_feedback', {})

    context = {
        'event': event,
        'registration': registration,
        'existing_feedback': existing_feedback,
    }
    return render(request, 'participant/event_feedback.html', context)


# =============================================================================
# PRIORITY 8: Notifications
# =============================================================================

@login_required
def notifications_list(request):
    """View all notifications"""
    from .models import AttendeeNotification

    user = request.user
    filter_type = request.GET.get('filter', 'all')

    notifications = AttendeeNotification.objects.filter(user=user)
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    unread_count = AttendeeNotification.objects.filter(user=user, is_read=False).count()

    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'unread_count': unread_count,
    }
    return render(request, 'participant/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    from .models import AttendeeNotification

    notification = get_object_or_404(AttendeeNotification, id=notification_id, user=request.user)
    notification.mark_read()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('attendee:notifications')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    from .models import AttendeeNotification

    AttendeeNotification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, 'All notifications marked as read.')
    return redirect('attendee:notifications')


# =============================================================================
# PRIORITY 9: Schedule Export
# =============================================================================

@login_required
def export_schedule_ical(request):
    """Export personal schedule to iCal format"""
    user = request.user
    now = timezone.now()

    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email),
        event__start_date__gte=now,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')

    cal_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//EventPortal//Schedule//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for reg in registrations:
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions, event=reg.event
            ).order_by('start_time')
            for session in sessions:
                cal_lines.extend([
                    "BEGIN:VEVENT",
                    f"DTSTART:{session.start_time.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{session.end_time.strftime('%Y%m%dT%H%M%SZ')}",
                    f"SUMMARY:{session.title}",
                    f"DESCRIPTION:{session.description[:200] if session.description else ''}",
                    f"LOCATION:{session.location or reg.event.venue_name or ''}",
                    "END:VEVENT",
                ])

    cal_lines.append("END:VCALENDAR")

    response = HttpResponse('\r\n'.join(cal_lines), content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename="my_schedule.ics"'
    return response


# =============================================================================
# PROFILE AND SETTINGS VIEWS
# =============================================================================

@login_required
def attendee_profile_edit(request):
    """Enhanced profile editing view"""
    user = request.user
    
    if request.method == 'POST':
        # Handle profile updates
        try:
            # Update basic fields
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.phone = request.POST.get('phone', '').strip()
            user.company = request.POST.get('company', '').strip()
            user.job_title = request.POST.get('job_title', '').strip()
            user.bio = request.POST.get('bio', '').strip()
            user.linkedin_url = request.POST.get('linkedin_url', '').strip()
            user.website = request.POST.get('website', '').strip()
            
            # Handle profile image upload
            if 'profile_image' in request.FILES:
                user.profile_image = request.FILES['profile_image']
            
            user.save()
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
            else:
                messages.success(request, 'Profile updated successfully!')
                return redirect('attendee:profile')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error updating profile: {str(e)}')
    
    # Get profile stats
    try:
        all_registrations = Registration.objects.filter(
            models.Q(user=user) | models.Q(attendee_email=user.email)
        )
        
        now = timezone.now()
        events_attended = all_registrations.filter(
            event__end_date__lt=now,
            status=RegistrationStatus.CHECKED_IN
        ).count()
        
        upcoming_events = all_registrations.filter(
            event__start_date__gte=now,
            status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
        ).count()
    except:
        events_attended = 0
        upcoming_events = 0
    
    # Get certificates count (placeholder)
    certificates_count = 0
    
    context = {
        'user': user,
        'events_attended': events_attended,
        'upcoming_events': upcoming_events,
        'certificates_count': certificates_count,
    }
    
    return render(request, 'participant/profile.html', context)


@login_required
def account_settings(request):
    """Account settings view with tabs for different settings categories"""
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action', 'change_password')  # Default action
        
        if action == 'change_password':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not current_password or not new_password or not confirm_password:
                return JsonResponse({'success': False, 'error': 'All password fields are required'})
            
            if not user.check_password(current_password):
                return JsonResponse({'success': False, 'error': 'Current password is incorrect'})
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'error': 'New passwords do not match'})
            
            if len(new_password) < 8:
                return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long'})
            
            try:
                user.set_password(new_password)
                user.save()
                return JsonResponse({'success': True, 'message': 'Password updated successfully!'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating password: {str(e)}'})
        
        elif action == 'update_notifications':
            # Handle notification preferences
            try:
                # Get notification preferences from form
                event_reminders = request.POST.get('event_reminders') == 'on'
                ticket_confirmations = request.POST.get('ticket_confirmations') == 'on'
                event_updates = request.POST.get('event_updates') == 'on'
                marketing_notifications = request.POST.get('marketing_notifications') == 'on'
                weekly_newsletter = request.POST.get('weekly_newsletter') == 'on'
                
                # Update user notification preferences (you can store this in user.notification_preferences JSON field)
                if not user.notification_preferences:
                    user.notification_preferences = {}
                
                user.notification_preferences.update({
                    'event_reminders': event_reminders,
                    'ticket_confirmations': ticket_confirmations,
                    'event_updates': event_updates,
                    'marketing_notifications': marketing_notifications,
                    'weekly_newsletter': weekly_newsletter,
                })
                user.save()
                
                return JsonResponse({'success': True, 'message': 'Notification preferences updated!'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating notifications: {str(e)}'})
        
        elif action == 'update_privacy':
            # Handle privacy settings
            try:
                public_profile = request.POST.get('public_profile') == 'on'
                hide_email = request.POST.get('hide_email') == 'on'
                hide_phone = request.POST.get('hide_phone') == 'on'
                analytics_sharing = request.POST.get('analytics_sharing') == 'on'
                
                # Update user privacy preferences
                if not user.notification_preferences:
                    user.notification_preferences = {}
                
                user.notification_preferences.update({
                    'public_profile': public_profile,
                    'hide_email': hide_email,
                    'hide_phone': hide_phone,
                    'analytics_sharing': analytics_sharing,
                })
                user.save()
                
                return JsonResponse({'success': True, 'message': 'Privacy settings updated!'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating privacy settings: {str(e)}'})
        
        elif action == 'update_preferences':
            # Handle general preferences
            try:
                language = request.POST.get('language', 'en')
                timezone_pref = request.POST.get('timezone', 'UTC')
                theme = request.POST.get('theme', 'light')
                email_format = request.POST.get('email_format', 'html')
                
                # Update user general preferences
                if not user.notification_preferences:
                    user.notification_preferences = {}
                
                user.notification_preferences.update({
                    'language': language,
                    'timezone': timezone_pref,
                    'theme': theme,
                    'email_format': email_format,
                })
                user.save()
                
                return JsonResponse({'success': True, 'message': 'Preferences updated!'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating preferences: {str(e)}'})
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    # Get current preferences for display
    preferences = user.notification_preferences or {}
    
    context = {
        'user': user,
        'preferences': preferences,
    }
    
    return render(request, 'participant/account_settings.html', context)