"""
WebSocket utilities for real-time theme generation notifications.

This module provides functions to send WebSocket notifications for theme generation
status updates, completion events, and error notifications.

Note: This implementation uses a simple approach that can be enhanced with
Django Channels for full WebSocket support in production.
"""

import json
import logging
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from events.models import Event

logger = logging.getLogger(__name__)
User = get_user_model()


class WebSocketNotificationManager:
    """
    Manager class for handling WebSocket notifications.
    
    In a production environment, this would integrate with Django Channels
    or another WebSocket framework to send real-time notifications to clients.
    """
    
    @staticmethod
    def get_event_channel_name(event_id):
        """Get the channel name for an event"""
        return f"event_{event_id}_theme_updates"
    
    @staticmethod
    def get_user_channel_name(user_id):
        """Get the channel name for a user"""
        return f"user_{user_id}_notifications"
    
    @staticmethod
    def store_notification(channel_name, message):
        """
        Store notification in cache for retrieval by clients.
        
        In production, this would be replaced by actual WebSocket sending.
        """
        # Store in cache with 1 hour expiration
        cache_key = f"websocket_notifications_{channel_name}"
        notifications = cache.get(cache_key, [])
        
        # Add timestamp to message
        message['timestamp'] = timezone.now().isoformat()
        notifications.append(message)
        
        # Keep only last 50 notifications
        notifications = notifications[-50:]
        
        cache.set(cache_key, notifications, 3600)  # 1 hour
        
        logger.info(f"Stored WebSocket notification for {channel_name}: {message['event']}")
    
    @staticmethod
    def get_notifications(channel_name, since=None):
        """
        Get stored notifications for a channel.
        
        Args:
            channel_name: The channel to get notifications for
            since: Optional datetime to get notifications since
        
        Returns:
            List of notification messages
        """
        cache_key = f"websocket_notifications_{channel_name}"
        notifications = cache.get(cache_key, [])
        
        if since:
            # Filter notifications since the given time
            since_str = since.isoformat()
            notifications = [
                n for n in notifications 
                if n.get('timestamp', '') > since_str
            ]
        
        return notifications


def notify_theme_generation_status(event_id, status, progress_percentage=None, 
                                 estimated_completion=None, error_message=None, 
                                 theme_id=None, user_id=None):
    """
    Send WebSocket notification for theme generation status updates.
    
    Args:
        event_id: ID of the event
        status: Generation status ('pending', 'processing', 'completed', 'failed')
        progress_percentage: Optional progress percentage (0-100)
        estimated_completion: Optional estimated completion datetime
        error_message: Optional error message for failed status
        theme_id: Optional theme ID for completed status
        user_id: Optional user ID to send user-specific notifications
    """
    try:
        # Validate event exists
        event = Event.objects.get(id=event_id)
        
        # Create base message
        message = {
            'event': 'theme_generation_status',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'status': status,
            }
        }
        
        # Add optional fields
        if progress_percentage is not None:
            message['data']['progress_percentage'] = progress_percentage
        
        if estimated_completion:
            message['data']['estimated_completion'] = estimated_completion.isoformat()
        
        if error_message:
            message['data']['error_message'] = error_message
        
        if theme_id:
            message['data']['theme_id'] = theme_id
        
        # Send to event channel (all users interested in this event)
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        # Send to user channel if specified
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        # Also send to event organizer
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent theme generation status notification: {status} for event {event_id}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send theme generation status notification: {str(e)}")


def notify_theme_generation_completed(event_id, theme_id, success=True, 
                                    preview_url=None, processing_time_ms=None,
                                    extraction_confidence=None, user_id=None):
    """
    Send WebSocket notification when theme generation is completed.
    
    Args:
        event_id: ID of the event
        theme_id: ID of the generated theme
        success: Whether generation was successful
        preview_url: Optional preview URL
        processing_time_ms: Optional processing time in milliseconds
        extraction_confidence: Optional extraction confidence score
        user_id: Optional user ID to send user-specific notifications
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'theme_generation_completed',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'theme_id': theme_id,
                'success': success,
            }
        }
        
        # Add optional fields
        if preview_url:
            message['data']['preview_url'] = preview_url
        
        if processing_time_ms is not None:
            message['data']['processing_time_ms'] = processing_time_ms
        
        if extraction_confidence is not None:
            message['data']['extraction_confidence'] = extraction_confidence
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent theme generation completed notification for event {event_id}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send theme generation completed notification: {str(e)}")


def notify_theme_generation_failed(event_id, error_message, user_id=None, 
                                 fallback_applied=False):
    """
    Send WebSocket notification when theme generation fails.
    
    Args:
        event_id: ID of the event
        error_message: Error message describing the failure
        user_id: Optional user ID to send user-specific notifications
        fallback_applied: Whether a fallback theme was applied
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'theme_generation_failed',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'error_message': error_message,
                'fallback_applied': fallback_applied,
            }
        }
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent theme generation failed notification for event {event_id}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send theme generation failed notification: {str(e)}")


def notify_theme_preview_updated(event_id, portal_type, theme_id, user_id=None):
    """
    Send WebSocket notification when theme preview is updated.
    
    Args:
        event_id: ID of the event
        portal_type: Type of portal ('staff', 'participant', 'organizer')
        theme_id: ID of the theme
        user_id: Optional user ID to send user-specific notifications
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'theme_preview_updated',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'portal_type': portal_type,
                'theme_id': theme_id,
                'preview_url': f'/api/v1/events/{event_id}/theme/preview/{portal_type}/',
            }
        }
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent theme preview updated notification for event {event_id}, portal {portal_type}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send theme preview updated notification: {str(e)}")


def notify_cache_cleared(event_id, user_id=None, entries_cleared=0):
    """
    Send WebSocket notification when theme cache is cleared.
    
    Args:
        event_id: ID of the event
        user_id: Optional user ID to send user-specific notifications
        entries_cleared: Number of cache entries cleared
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'theme_cache_cleared',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'entries_cleared': entries_cleared,
            }
        }
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent cache cleared notification for event {event_id}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send cache cleared notification: {str(e)}")


# Utility functions for client-side polling (alternative to WebSocket)

def get_event_notifications(event_id, since=None):
    """
    Get notifications for an event (for client-side polling).
    
    Args:
        event_id: ID of the event
        since: Optional datetime to get notifications since
    
    Returns:
        List of notification messages
    """
    channel_name = WebSocketNotificationManager.get_event_channel_name(event_id)
    return WebSocketNotificationManager.get_notifications(channel_name, since)


def get_user_notifications(user_id, since=None):
    """
    Get notifications for a user (for client-side polling).
    
    Args:
        user_id: ID of the user
        since: Optional datetime to get notifications since
    
    Returns:
        List of notification messages
    """
    channel_name = WebSocketNotificationManager.get_user_channel_name(user_id)
    return WebSocketNotificationManager.get_notifications(channel_name, since)


def clear_event_notifications(event_id):
    """
    Clear all notifications for an event.
    
    Args:
        event_id: ID of the event
    """
    channel_name = WebSocketNotificationManager.get_event_channel_name(event_id)
    cache_key = f"websocket_notifications_{channel_name}"
    cache.delete(cache_key)
    logger.info(f"Cleared notifications for event {event_id}")


def clear_user_notifications(user_id):
    """
    Clear all notifications for a user.
    
    Args:
        user_id: ID of the user
    """
    channel_name = WebSocketNotificationManager.get_user_channel_name(user_id)
    cache_key = f"websocket_notifications_{channel_name}"
    cache.delete(cache_key)
    logger.info(f"Cleared notifications for user {user_id}")


# WebSocket connection simulation for development/testing
class MockWebSocketConnection:
    """
    Mock WebSocket connection for development and testing.
    
    In production, this would be replaced by actual WebSocket connections
    using Django Channels or similar framework.
    """
    
    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.is_connected = True
    
    def send(self, message):
        """Simulate sending a message over WebSocket"""
        if self.is_connected:
            WebSocketNotificationManager.store_notification(self.channel_name, message)
            logger.debug(f"Mock WebSocket sent message to {self.channel_name}: {message['event']}")
    
    def close(self):
        """Simulate closing the WebSocket connection"""
        self.is_connected = False
        logger.debug(f"Mock WebSocket connection closed for {self.channel_name}")
    
    def receive(self):
        """Simulate receiving messages from WebSocket"""
        if self.is_connected:
            return WebSocketNotificationManager.get_notifications(self.channel_name)
        return []


# Enhanced WebSocket notification functions for real-time updates

def notify_color_extraction_progress(event_id, progress_percentage, stage, user_id=None):
    """
    Send WebSocket notification for color extraction progress.
    
    Args:
        event_id: ID of the event
        progress_percentage: Progress percentage (0-100)
        stage: Current extraction stage
        user_id: Optional user ID to send user-specific notifications
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'color_extraction_progress',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'progress_percentage': progress_percentage,
                'stage': stage,
                'estimated_completion': (timezone.now() + timezone.timedelta(seconds=30)).isoformat()
            }
        }
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent color extraction progress notification: {progress_percentage}% for event {event_id}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send color extraction progress notification: {str(e)}")


def notify_theme_css_generated(event_id, theme_id, portal_type=None, user_id=None):
    """
    Send WebSocket notification when theme CSS is generated.
    
    Args:
        event_id: ID of the event
        theme_id: ID of the theme
        portal_type: Optional portal type for portal-specific CSS
        user_id: Optional user ID to send user-specific notifications
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'theme_css_generated',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'theme_id': theme_id,
                'portal_type': portal_type,
                'css_url': f'/api/v1/events/{event_id}/theme/preview/{portal_type}/?format=css' if portal_type else None
            }
        }
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent theme CSS generated notification for event {event_id}, theme {theme_id}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send theme CSS generated notification: {str(e)}")


def notify_accessibility_validation_completed(event_id, theme_id, wcag_compliant, 
                                            adjustments_made=None, user_id=None):
    """
    Send WebSocket notification when accessibility validation is completed.
    
    Args:
        event_id: ID of the event
        theme_id: ID of the theme
        wcag_compliant: Whether theme is WCAG compliant
        adjustments_made: List of adjustments made for compliance
        user_id: Optional user ID to send user-specific notifications
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'accessibility_validation_completed',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'theme_id': theme_id,
                'wcag_compliant': wcag_compliant,
                'adjustments_made': adjustments_made or [],
                'validation_status': 'passed' if wcag_compliant else 'failed'
            }
        }
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent accessibility validation notification for event {event_id}, compliant: {wcag_compliant}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send accessibility validation notification: {str(e)}")


def notify_theme_variation_created(event_id, theme_id, variation_id, variation_type, user_id=None):
    """
    Send WebSocket notification when a theme variation is created.
    
    Args:
        event_id: ID of the event
        theme_id: ID of the base theme
        variation_id: ID of the created variation
        variation_type: Type of variation created
        user_id: Optional user ID to send user-specific notifications
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'theme_variation_created',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'theme_id': theme_id,
                'variation_id': variation_id,
                'variation_type': variation_type,
                'preview_url': f'/api/v1/events/{event_id}/theme/variations/{variation_id}/'
            }
        }
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent theme variation created notification for event {event_id}, variation {variation_type}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send theme variation created notification: {str(e)}")


def notify_bulk_operation_progress(event_id, operation_type, progress_percentage, 
                                 completed_items, total_items, user_id=None):
    """
    Send WebSocket notification for bulk operation progress.
    
    Args:
        event_id: ID of the event
        operation_type: Type of bulk operation
        progress_percentage: Progress percentage (0-100)
        completed_items: Number of completed items
        total_items: Total number of items
        user_id: Optional user ID to send user-specific notifications
    """
    try:
        event = Event.objects.get(id=event_id)
        
        message = {
            'event': 'bulk_operation_progress',
            'data': {
                'event_id': event_id,
                'event_title': event.title,
                'operation_type': operation_type,
                'progress_percentage': progress_percentage,
                'completed_items': completed_items,
                'total_items': total_items,
                'estimated_completion': (timezone.now() + timezone.timedelta(
                    seconds=int((total_items - completed_items) * 10)
                )).isoformat() if completed_items < total_items else None
            }
        }
        
        # Send notifications
        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
        WebSocketNotificationManager.store_notification(event_channel, message)
        
        if user_id:
            user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
            WebSocketNotificationManager.store_notification(user_channel, message)
        
        if event.organizer_id and event.organizer_id != user_id:
            organizer_channel = WebSocketNotificationManager.get_user_channel_name(event.organizer_id)
            WebSocketNotificationManager.store_notification(organizer_channel, message)
        
        logger.info(f"Sent bulk operation progress notification: {operation_type} {progress_percentage}% for event {event_id}")
        
    except Event.DoesNotExist:
        logger.error(f"Cannot send notification: Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to send bulk operation progress notification: {str(e)}")


def notify_rate_limit_warning(user_id, operation_type, current_count, limit):
    """
    Send WebSocket notification when user is approaching rate limits.
    
    Args:
        user_id: ID of the user
        operation_type: Type of operation being rate limited
        current_count: Current number of operations
        limit: Rate limit threshold
    """
    try:
        message = {
            'event': 'rate_limit_warning',
            'data': {
                'user_id': user_id,
                'operation_type': operation_type,
                'current_count': current_count,
                'limit': limit,
                'remaining': limit - current_count,
                'warning_threshold': int(limit * 0.8)  # Warn at 80% of limit
            }
        }
        
        # Send to user channel only
        user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
        WebSocketNotificationManager.store_notification(user_channel, message)
        
        logger.info(f"Sent rate limit warning to user {user_id} for {operation_type}: {current_count}/{limit}")
        
    except Exception as e:
        logger.error(f"Failed to send rate limit warning notification: {str(e)}")


# Enhanced WebSocket connection management

class EnhancedWebSocketNotificationManager(WebSocketNotificationManager):
    """
    Enhanced WebSocket notification manager with additional features.
    """
    
    @staticmethod
    def get_global_channel_name():
        """Get the global channel name for system-wide notifications"""
        return "global_theme_updates"
    
    @staticmethod
    def get_portal_channel_name(portal_type):
        """Get the channel name for portal-specific notifications"""
        return f"portal_{portal_type}_updates"
    
    @staticmethod
    def broadcast_system_notification(message):
        """
        Broadcast a system-wide notification to all connected clients.
        
        Args:
            message: Notification message to broadcast
        """
        global_channel = EnhancedWebSocketNotificationManager.get_global_channel_name()
        WebSocketNotificationManager.store_notification(global_channel, message)
        logger.info(f"Broadcasted system notification: {message['event']}")
    
    @staticmethod
    def send_portal_notification(portal_type, message):
        """
        Send notification to all users of a specific portal type.
        
        Args:
            portal_type: Type of portal ('staff', 'participant', 'organizer')
            message: Notification message to send
        """
        portal_channel = EnhancedWebSocketNotificationManager.get_portal_channel_name(portal_type)
        WebSocketNotificationManager.store_notification(portal_channel, message)
        logger.info(f"Sent portal notification to {portal_type}: {message['event']}")
    
    @staticmethod
    def get_connection_stats():
        """
        Get statistics about WebSocket connections and notifications.
        
        Returns:
            Dict with connection statistics
        """
        from django.core.cache import cache
        
        # Get all notification cache keys
        cache_keys = cache.keys("websocket_notifications_*") if hasattr(cache, 'keys') else []
        
        stats = {
            'total_channels': len(cache_keys),
            'event_channels': len([k for k in cache_keys if 'event_' in k]),
            'user_channels': len([k for k in cache_keys if 'user_' in k]),
            'portal_channels': len([k for k in cache_keys if 'portal_' in k]),
            'global_channels': len([k for k in cache_keys if 'global_' in k]),
            'total_notifications': 0,
            'notification_types': {}
        }
        
        # Count notifications by type
        for cache_key in cache_keys:
            notifications = cache.get(cache_key, [])
            stats['total_notifications'] += len(notifications)
            
            for notification in notifications:
                event_type = notification.get('event', 'unknown')
                stats['notification_types'][event_type] = stats['notification_types'].get(event_type, 0) + 1
        
        return stats


# System maintenance functions

def cleanup_old_notifications(max_age_hours=24):
    """
    Clean up old WebSocket notifications from cache.
    
    Args:
        max_age_hours: Maximum age of notifications to keep (in hours)
    """
    try:
        from django.core.cache import cache
        
        cutoff_time = timezone.now() - timezone.timedelta(hours=max_age_hours)
        cutoff_str = cutoff_time.isoformat()
        
        # Get all notification cache keys
        cache_keys = cache.keys("websocket_notifications_*") if hasattr(cache, 'keys') else []
        
        cleaned_count = 0
        
        for cache_key in cache_keys:
            notifications = cache.get(cache_key, [])
            
            # Filter out old notifications
            fresh_notifications = [
                n for n in notifications 
                if n.get('timestamp', '') > cutoff_str
            ]
            
            if len(fresh_notifications) != len(notifications):
                cache.set(cache_key, fresh_notifications, 3600)  # Reset TTL
                cleaned_count += len(notifications) - len(fresh_notifications)
        
        logger.info(f"Cleaned up {cleaned_count} old WebSocket notifications")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup old notifications: {str(e)}")
        return 0


def get_notification_health_status():
    """
    Get health status of the WebSocket notification system.
    
    Returns:
        Dict with health status information
    """
    try:
        stats = EnhancedWebSocketNotificationManager.get_connection_stats()
        
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'statistics': stats,
            'issues': []
        }
        
        # Check for potential issues
        if stats['total_notifications'] > 10000:
            health_status['issues'].append('High notification count - consider cleanup')
            health_status['status'] = 'warning'
        
        if stats['total_channels'] > 1000:
            health_status['issues'].append('High channel count - monitor memory usage')
            if health_status['status'] == 'healthy':
                health_status['status'] = 'warning'
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to get notification health status: {str(e)}")
        return {
            'status': 'error',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }