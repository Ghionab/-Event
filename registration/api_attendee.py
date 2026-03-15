"""
REST API views for attendee AJAX functionality
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.db import models

from .models import (
    Registration, RegistrationStatus, AttendeePreference,
    SessionAttendance, AttendeeNotification
)
from events.models import Event, EventSession


@login_required
@require_POST
def toggle_saved_session(request, session_id):
    """Toggle a session in the user's saved sessions"""
    session = get_object_or_404(EventSession, id=session_id)
    user = request.user

    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).filter(
        event=session.event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()

    if not registration:
        return JsonResponse({'success': False, 'message': 'Not registered for this event.'}, status=403)

    prefs, _ = AttendeePreference.objects.get_or_create(
        user=user, event=session.event, defaults={'saved_sessions': []}
    )

    saved = prefs.saved_sessions or []
    if session_id in saved:
        saved.remove(session_id)
        action = 'removed'
    else:
        saved.append(session_id)
        action = 'added'

    prefs.saved_sessions = saved
    prefs.save()

    return JsonResponse({'success': True, 'action': action, 'session_id': session_id})


@login_required
@require_POST
def submit_session_rating(request, session_id):
    """Submit a rating and feedback for a session"""
    import json

    session = get_object_or_404(EventSession, id=session_id)
    user = request.user

    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).filter(
        event=session.event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()

    if not registration:
        return JsonResponse({'success': False, 'message': 'Not registered for this event.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    rating = data.get('rating')
    feedback = data.get('feedback', '')

    if not rating or int(rating) < 1 or int(rating) > 5:
        return JsonResponse({'success': False, 'message': 'Rating must be between 1 and 5.'}, status=400)

    attendance, _ = SessionAttendance.objects.get_or_create(
        registration=registration, session=session
    )
    attendance.rating = int(rating)
    attendance.feedback = feedback
    attendance.save()

    return JsonResponse({'success': True, 'message': 'Rating submitted successfully.'})


@login_required
@require_GET
def dashboard_data(request):
    """Get dashboard data as JSON"""
    user = request.user
    now = timezone.now()

    all_regs = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email=user.email)
    ).select_related('event', 'ticket_type')

    upcoming = all_regs.filter(
        event__start_date__gte=now,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    )

    past = all_regs.filter(event__start_date__lt=now)

    from .models import AttendeeMessage
    unread_messages = AttendeeMessage.objects.filter(recipient=user, is_read=False).count()
    unread_notifications = AttendeeNotification.objects.filter(user=user, is_read=False).count()

    return JsonResponse({
        'stats': {
            'total_events': all_regs.count(),
            'upcoming_events': upcoming.count(),
            'past_events': past.filter(status=RegistrationStatus.CHECKED_IN).count(),
            'unread_messages': unread_messages,
            'unread_notifications': unread_notifications,
        },
        'upcoming': [
            {
                'id': r.id,
                'event_title': r.event.title,
                'event_date': r.event.start_date.isoformat(),
                'venue': r.event.venue_name or 'Virtual',
                'status': r.status,
                'ticket_type': r.ticket_type.name if r.ticket_type else None,
            } for r in upcoming[:5]
        ],
    })


@login_required
@require_GET
def registrations_list(request):
    """Get registrations list as JSON"""
    user = request.user

    regs = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
    ).select_related('event', 'ticket_type').order_by('-created_at')

    filter_type = request.GET.get('filter', 'all')
    now = timezone.now()
    if filter_type == 'upcoming':
        regs = regs.filter(event__start_date__gte=now)
    elif filter_type == 'past':
        regs = regs.filter(event__start_date__lt=now)
    elif filter_type == 'cancelled':
        regs = regs.filter(status=RegistrationStatus.CANCELLED)

    return JsonResponse({
        'registrations': [
            {
                'id': r.id,
                'registration_number': r.registration_number,
                'event_title': r.event.title,
                'event_date': r.event.start_date.isoformat(),
                'status': r.status,
                'status_display': r.get_status_display(),
                'ticket_type': r.ticket_type.name if r.ticket_type else None,
                'total_amount': str(r.total_amount),
            } for r in regs[:50]
        ],
    })


@login_required
@require_GET
def notifications_list(request):
    """Get notifications as JSON"""
    user = request.user
    filter_type = request.GET.get('filter', 'all')

    notifications = AttendeeNotification.objects.filter(user=user)
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)

    return JsonResponse({
        'notifications': [
            {
                'id': n.id,
                'type': n.notification_type,
                'title': n.title,
                'message': n.message,
                'is_read': n.is_read,
                'link': n.link,
                'created_at': n.created_at.isoformat(),
            } for n in notifications[:50]
        ],
        'unread_count': AttendeeNotification.objects.filter(user=user, is_read=False).count(),
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a notification as read via API"""
    notification = get_object_or_404(AttendeeNotification, id=notification_id, user=request.user)
    notification.mark_read()
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read"""
    AttendeeNotification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())
    return JsonResponse({'success': True})
