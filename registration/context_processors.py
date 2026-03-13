"""
Context processors for attendee portal navigation badges
"""
from .models import AttendeeMessage, AttendeeNotification


def attendee_context(request):
    """Add unread counts for messages and notifications to template context"""
    if not request.user.is_authenticated:
        return {}

    unread_messages_qs = AttendeeMessage.objects.filter(
        recipient=request.user,
        is_read=False
    )
    unread_messages_count = unread_messages_qs.count()

    unread_notifications_qs = AttendeeNotification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')
    unread_notifications_count = unread_notifications_qs.count()

    # Get the latest 5 unread notifications for the dropdown
    recent_notifications = unread_notifications_qs[:5]

    return {
        'unread_messages_count': unread_messages_count,
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
    }
