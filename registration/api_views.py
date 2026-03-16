"""
API views for calendar synchronization
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta

from .models import Registration, RegistrationStatus, AttendeePreference, SessionAttendance
from events.models import Event, EventSession


@login_required
@require_http_methods(["GET"])
def calendar_events_api(request):
    """API endpoint to get calendar events in JSON format"""
    user = request.user
    now = timezone.now()
    
    # Get query parameters
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    event_type = request.GET.get('event_type')
    
    # Parse dates
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=30)
    
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            end_date = now + timedelta(days=365)
    else:
        end_date = now + timedelta(days=365)
    
    # Get upcoming registrations
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        event__start_date__gte=start_date,
        event__end_date__lte=end_date,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')
    
    # Apply event type filter
    if event_type:
        registrations = registrations.filter(event__event_type=event_type)
    
    # Build calendar events
    calendar_events = []
    
    for reg in registrations:
        # Add registered events
        calendar_events.append({
            'id': f"event_{reg.event.id}",
            'title': reg.event.title,
            'start': reg.event.start_date.isoformat(),
            'end': reg.event.end_date.isoformat(),
            'allDay': True,
            'extendedProps': {
                'type': 'registered',
                'event_title': reg.event.title,
                'event_id': reg.event.id,
                'event_type': reg.event.event_type,
                'location': reg.event.venue_name or 'Virtual',
                'description': reg.event.description,
                'registration_id': reg.id,
                'color': '#10b981'
            }
        })
        
        # Get saved sessions
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions,
                event=reg.event,
                start_time__gte=start_date,
                end_time__lte=end_date
            ).select_related('event').prefetch_related('speakers')
            
            for session in sessions:
                speakers = ', '.join([speaker.name for speaker in session.speakers.all()])
                calendar_events.append({
                    'id': f"session_{session.id}",
                    'title': session.title,
                    'start': session.start_time.isoformat(),
                    'end': session.end_time.isoformat(),
                    'allDay': False,
                    'extendedProps': {
                        'type': 'saved',
                        'event_title': reg.event.title,
                        'event_id': reg.event.id,
                        'session_id': session.id,
                        'event_type': reg.event.event_type,
                        'location': session.location or reg.event.venue_name,
                        'speakers': speakers,
                        'description': session.description or '',
                        'feedback_url': f"/attendee/session/{session.id}/feedback/",
                        'color': '#3b82f6'
                    }
                })
    
    return JsonResponse({
        'success': True,
        'events': calendar_events,
        'total': len(calendar_events)
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def save_session_api(request):
    """API endpoint to save/unsave a session"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        action = data.get('action')  # 'save' or 'unsave'
        
        if not session_id or not action:
            return JsonResponse({
                'success': False,
                'message': 'Missing session_id or action'
            })
        
        session = get_object_or_404(EventSession, id=session_id)
        user = request.user
        
        # Check if user is registered for the event
        registration = Registration.objects.filter(
            models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
        ).filter(
            event=session.event,
            status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
        ).first()
        
        if not registration:
            return JsonResponse({
                'success': False,
                'message': 'You must be registered for this event.'
            })
        
        # Get or create preferences
        prefs, created = AttendeePreference.objects.get_or_create(
            user=user,
            event=session.event,
            defaults={'saved_sessions': []}
        )
        
        # Update saved sessions
        saved_sessions = prefs.saved_sessions or []
        
        if action == 'save' and session_id not in saved_sessions:
            saved_sessions.append(session_id)
            message = 'Session saved to your schedule'
        elif action == 'unsave' and session_id in saved_sessions:
            saved_sessions.remove(session_id)
            message = 'Session removed from your schedule'
        else:
            message = 'No changes made'
        
        prefs.saved_sessions = saved_sessions
        prefs.save()
        
        # Send WebSocket notification
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"calendar_{user.id}",
            {
                'type': 'session_added' if action == 'save' else 'session_removed',
                'event': {
                    'id': f"session_{session.id}",
                    'title': session.title,
                    'start': session.start_time.isoformat(),
                    'end': session.end_time.isoformat(),
                    'extendedProps': {
                        'type': 'saved',
                        'event_title': session.event.title,
                        'event_id': session.event.id,
                        'session_id': session.id,
                        'location': session.location,
                        'description': session.description or ''
                    }
                } if action == 'save' else None,
                'event_id': f"session_{session_id}" if action == 'unsave' else None
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': message,
            'action': action,
            'session_id': session_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def calendar_conflicts_api(request):
    """API endpoint to detect schedule conflicts"""
    user = request.user
    now = timezone.now()
    
    # Get upcoming registrations
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        event__start_date__gte=now,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')
    
    # Get all saved sessions
    all_sessions = []
    for reg in registrations:
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions,
                event=reg.event
            ).select_related('event')
            
            for session in sessions:
                all_sessions.append(session)
    
    # Sort by start time
    all_sessions.sort(key=lambda x: x.start_time)
    
    # Detect conflicts
    conflicts = []
    for i, session in enumerate(all_sessions):
        for j, other in enumerate(all_sessions[i+1:], i+1):
            if session.start_time < other.end_time and session.end_time > other.start_time:
                conflicts.append({
                    'session1': {
                        'id': session.id,
                        'title': session.title,
                        'start': session.start_time.isoformat(),
                        'end': session.end_time.isoformat(),
                        'event': session.event.title
                    },
                    'session2': {
                        'id': other.id,
                        'title': other.title,
                        'start': other.start_time.isoformat(),
                        'end': other.end_time.isoformat(),
                        'event': other.event.title
                    }
                })
    
    return JsonResponse({
        'success': True,
        'conflicts': conflicts,
        'total_conflicts': len(conflicts)
    })


@login_required
@require_http_methods(["GET"])
def calendar_stats_api(request):
    """API endpoint to get calendar statistics"""
    user = request.user
    now = timezone.now()
    
    # Get registrations
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')
    
    # Separate upcoming and past
    upcoming_registrations = registrations.filter(event__start_date__gte=now)
    past_registrations = registrations.filter(event__start_date__lt=now)
    
    # Count saved sessions
    saved_sessions_count = 0
    upcoming_events = []
    
    for reg in upcoming_registrations:
        upcoming_events.append({
            'id': reg.event.id,
            'title': reg.event.title,
            'start_date': reg.event.start_date.isoformat(),
            'event_type': reg.event.event_type
        })
        
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            saved_sessions_count += len(prefs.saved_sessions)
    
    # Get conflicts
    conflict_count = 0
    all_sessions = []
    for reg in upcoming_registrations:
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions,
                event=reg.event
            )
            all_sessions.extend(sessions)
    
    # Detect conflicts
    for i, session in enumerate(all_sessions):
        for j, other in enumerate(all_sessions[i+1:], i+1):
            if session.start_time < other.end_time and session.end_time > other.start_time:
                conflict_count += 1
    
    return JsonResponse({
        'success': True,
        'stats': {
            'total_events': registrations.count(),
            'upcoming_events': upcoming_registrations.count(),
            'past_events': past_registrations.count(),
            'saved_sessions': saved_sessions_count,
            'conflicts': conflict_count,
            'upcoming_events_list': upcoming_events[:5]  # Next 5 events
        }
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def calendar_sync_external(request):
    """API endpoint to sync with external calendars"""
    try:
        data = json.loads(request.body)
        calendar_type = data.get('calendar_type')  # 'google' or 'outlook'
        sync_action = data.get('action')  # 'import' or 'export'
        
        if calendar_type not in ['google', 'outlook']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid calendar type'
            })
        
        if sync_action not in ['import', 'export']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid sync action'
            })
        
        # This would integrate with Google Calendar API or Microsoft Graph API
        # For now, return a placeholder response
        
        if sync_action == 'import':
            return JsonResponse({
                'success': True,
                'message': f'Import from {calendar_type.title()} calendar completed',
                'imported_events': 0  # Would be actual count
            })
        else:
            return JsonResponse({
                'success': True,
                'message': f'Export to {calendar_type.title()} calendar completed',
                'export_url': f'/api/calendar/export/{calendar_type}/'  # Would be actual URL
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
