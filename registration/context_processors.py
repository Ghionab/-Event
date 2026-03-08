"""
Context processors for attendee portal navigation badges
"""
from .models import AttendeeMessage, AttendeeNotification


def attendee_context(request):
    """Add unread counts for messages and notifications to template context"""
    if not request.user.is_authenticated:
        return {}

    unread_messages = AttendeeMessage.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    unread_notifications = AttendeeNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return {
        'unread_messages_count': unread_messages,
        'unread_notifications_count': unread_notifications,
    }
