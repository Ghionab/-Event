"""
WebSocket-related API views for real-time theme generation notifications.

These views provide REST endpoints for clients to receive real-time updates
about theme generation status, either through polling or WebSocket connections.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from events.models import Event
from .websocket_utils import (
    get_event_notifications, get_user_notifications,
    clear_event_notifications, clear_user_notifications,
    WebSocketNotificationManager
)
from .serializers import WebSocketEventSerializer, ThemeGenerationStatusSerializer
from .permissions import IsEventOwnerOrReadOnly
import logging

logger = logging.getLogger(__name__)


class EventNotificationsAPIView(APIView):
    """
    Get real-time notifications for an event.
    
    This endpoint allows clients to poll for theme generation updates
    and other real-time notifications related to an event.
    """
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def get(self, request, event_id):
        """Get notifications for an event"""
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to view notifications for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get 'since' parameter for incremental updates
        since_param = request.GET.get('since')
        since = None
        if since_param:
            try:
                since = parse_datetime(since_param)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid since parameter. Use ISO 8601 format.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            # Get notifications for the event
            notifications = get_event_notifications(event_id, since)
            
            # Serialize notifications
            serializer = WebSocketEventSerializer(notifications, many=True)
            
            return Response({
                'event_id': event_id,
                'event_title': event.title,
                'notifications': serializer.data,
                'count': len(notifications),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get notifications for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Failed to retrieve notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, event_id):
        """Clear notifications for an event"""
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to clear notifications for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            clear_event_notifications(event_id)
            
            return Response({
                'success': True,
                'message': f'Cleared notifications for event {event.title}',
                'event_id': event_id
            })
            
        except Exception as e:
            logger.error(f"Failed to clear notifications for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Failed to clear notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserNotificationsAPIView(APIView):
    """
    Get real-time notifications for the authenticated user.
    
    This endpoint allows users to receive all their theme-related notifications
    across all events they have access to.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get notifications for the authenticated user"""
        user_id = request.user.id
        
        # Get 'since' parameter for incremental updates
        since_param = request.GET.get('since')
        since = None
        if since_param:
            try:
                since = parse_datetime(since_param)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid since parameter. Use ISO 8601 format.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            # Get notifications for the user
            notifications = get_user_notifications(user_id, since)
            
            # Serialize notifications
            serializer = WebSocketEventSerializer(notifications, many=True)
            
            return Response({
                'user_id': user_id,
                'notifications': serializer.data,
                'count': len(notifications),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get notifications for user {user_id}: {str(e)}")
            return Response(
                {'error': f'Failed to retrieve notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request):
        """Clear notifications for the authenticated user"""
        user_id = request.user.id
        
        try:
            clear_user_notifications(user_id)
            
            return Response({
                'success': True,
                'message': 'Cleared all notifications for user',
                'user_id': user_id
            })
            
        except Exception as e:
            logger.error(f"Failed to clear notifications for user {user_id}: {str(e)}")
            return Response(
                {'error': f'Failed to clear notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeGenerationStatusAPIView(APIView):
    """
    Get the current status of theme generation for an event.
    
    This endpoint provides the current status of any ongoing theme generation
    process for an event.
    """
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def get(self, request, event_id):
        """Get theme generation status for an event"""
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to view generation status for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get recent notifications to determine current status
            notifications = get_event_notifications(event_id)
            
            # Find the most recent theme generation status notification
            current_status = {
                'event_id': event_id,
                'status': 'unknown',
                'progress_percentage': 0,
                'last_update': None
            }
            
            for notification in reversed(notifications):  # Most recent first
                if notification.get('event') == 'theme_generation_status':
                    data = notification.get('data', {})
                    current_status.update({
                        'status': data.get('status', 'unknown'),
                        'progress_percentage': data.get('progress_percentage', 0),
                        'estimated_completion': data.get('estimated_completion'),
                        'error_message': data.get('error_message'),
                        'theme_id': data.get('theme_id'),
                        'last_update': notification.get('timestamp')
                    })
                    break
            
            # Check if there's an existing theme
            from .models import EventTheme
            try:
                theme = EventTheme.objects.get(event=event)
                current_status['has_theme'] = True
                current_status['theme_id'] = theme.id
                current_status['theme_created'] = theme.created_at.isoformat()
                current_status['theme_updated'] = theme.updated_at.isoformat()
            except EventTheme.DoesNotExist:
                current_status['has_theme'] = False
            
            serializer = ThemeGenerationStatusSerializer(data=current_status)
            serializer.is_valid(raise_exception=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Failed to get generation status for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Failed to retrieve generation status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebSocketConnectionInfoAPIView(APIView):
    """
    Get WebSocket connection information for real-time updates.
    
    This endpoint provides clients with the information needed to establish
    WebSocket connections for real-time notifications.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get WebSocket connection information"""
        user_id = request.user.id
        
        # Get event IDs the user has access to
        user_events = Event.objects.filter(organizer=request.user).values_list('id', flat=True)
        
        connection_info = {
            'user_id': user_id,
            'user_channel': WebSocketNotificationManager.get_user_channel_name(user_id),
            'event_channels': [
                {
                    'event_id': event_id,
                    'channel_name': WebSocketNotificationManager.get_event_channel_name(event_id)
                }
                for event_id in user_events
            ],
            'websocket_url': request.build_absolute_uri('/ws/'),  # Would be actual WebSocket URL
            'polling_endpoints': {
                'user_notifications': request.build_absolute_uri('/api/v1/notifications/user/'),
                'event_notifications': request.build_absolute_uri('/api/v1/notifications/events/{event_id}/'),
                'generation_status': request.build_absolute_uri('/api/v1/events/{event_id}/theme/status/')
            },
            'recommended_poll_interval_ms': 5000,  # 5 seconds
            'supported_events': [
                'theme_generation_status',
                'theme_generation_completed',
                'theme_generation_failed',
                'theme_preview_updated',
                'theme_cache_cleared'
            ]
        }
        
        return Response(connection_info)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def simulate_websocket_event(request):
    """
    Simulate a WebSocket event for testing purposes.
    
    This endpoint is only available in development mode and allows
    testing of WebSocket notification functionality.
    """
    from django.conf import settings
    
    # Only allow in debug mode
    if not settings.DEBUG:
        return Response(
            {'error': 'This endpoint is only available in debug mode'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    event_type = request.data.get('event_type')
    event_id = request.data.get('event_id')
    data = request.data.get('data', {})
    
    if not event_type or not event_id:
        return Response(
            {'error': 'event_type and event_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Import notification functions
        from .websocket_utils import (
            notify_theme_generation_status,
            notify_theme_generation_completed,
            notify_theme_generation_failed,
            notify_theme_preview_updated
        )
        
        # Send appropriate notification based on event type
        if event_type == 'theme_generation_status':
            notify_theme_generation_status(
                event_id=event_id,
                status=data.get('status', 'processing'),
                progress_percentage=data.get('progress_percentage'),
                user_id=request.user.id
            )
        elif event_type == 'theme_generation_completed':
            notify_theme_generation_completed(
                event_id=event_id,
                theme_id=data.get('theme_id', 1),
                success=data.get('success', True),
                user_id=request.user.id
            )
        elif event_type == 'theme_generation_failed':
            notify_theme_generation_failed(
                event_id=event_id,
                error_message=data.get('error_message', 'Test error'),
                user_id=request.user.id
            )
        elif event_type == 'theme_preview_updated':
            notify_theme_preview_updated(
                event_id=event_id,
                portal_type=data.get('portal_type', 'staff'),
                theme_id=data.get('theme_id', 1),
                user_id=request.user.id
            )
        else:
            return Response(
                {'error': f'Unsupported event type: {event_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'success': True,
            'message': f'Simulated {event_type} event for event {event_id}',
            'event_type': event_type,
            'event_id': event_id
        })
        
    except Exception as e:
        logger.error(f"Failed to simulate WebSocket event: {str(e)}")
        return Response(
            {'error': f'Failed to simulate event: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def websocket_health_check(request):
    """
    Health check endpoint for WebSocket functionality.
    
    This endpoint can be used to verify that the WebSocket notification
    system is working correctly.
    """
    try:
        # Test notification storage and retrieval
        test_channel = f"test_channel_{request.user.id}"
        test_message = {
            'event': 'health_check',
            'data': {
                'test': True,
                'user_id': request.user.id,
                'timestamp': timezone.now().isoformat()
            }
        }
        
        # Store test notification
        WebSocketNotificationManager.store_notification(test_channel, test_message)
        
        # Retrieve test notification
        notifications = WebSocketNotificationManager.get_notifications(test_channel)
        
        # Check if our test message is there
        health_status = {
            'websocket_system': 'operational',
            'notification_storage': 'working',
            'test_message_stored': len(notifications) > 0,
            'timestamp': timezone.now().isoformat()
        }
        
        # Clean up test notification
        from django.core.cache import cache
        cache_key = f"websocket_notifications_{test_channel}"
        cache.delete(cache_key)
        
        return Response(health_status)
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {str(e)}")
        return Response({
            'websocket_system': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SystemNotificationsAPIView(APIView):
    """
    Get system-wide notifications for administrators.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get system-wide notifications"""
        # Only allow staff users to view system notifications
        if not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to view system notifications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from .websocket_utils import EnhancedWebSocketNotificationManager
            
            # Get global notifications
            global_channel = EnhancedWebSocketNotificationManager.get_global_channel_name()
            notifications = EnhancedWebSocketNotificationManager.get_notifications(global_channel)
            
            # Get system statistics
            stats = EnhancedWebSocketNotificationManager.get_connection_stats()
            
            return Response({
                'notifications': notifications,
                'statistics': stats,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get system notifications: {str(e)}")
            return Response(
                {'error': f'Failed to retrieve system notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PortalNotificationsAPIView(APIView):
    """
    Get portal-specific notifications.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, portal_type):
        """Get notifications for a specific portal type"""
        valid_portals = ['staff', 'participant', 'organizer']
        if portal_type not in valid_portals:
            return Response(
                {'error': f'Invalid portal type. Must be one of: {", ".join(valid_portals)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .websocket_utils import EnhancedWebSocketNotificationManager
            
            # Get portal-specific notifications
            portal_channel = EnhancedWebSocketNotificationManager.get_portal_channel_name(portal_type)
            notifications = EnhancedWebSocketNotificationManager.get_notifications(portal_channel)
            
            return Response({
                'portal_type': portal_type,
                'notifications': notifications,
                'count': len(notifications),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get portal notifications for {portal_type}: {str(e)}")
            return Response(
                {'error': f'Failed to retrieve portal notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationHealthAPIView(APIView):
    """
    Get health status of the notification system.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get notification system health status"""
        # Only allow staff users to view health status
        if not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to view system health'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from .websocket_utils import get_notification_health_status
            
            health_status = get_notification_health_status()
            
            return Response(health_status)
            
        except Exception as e:
            logger.error(f"Failed to get notification health status: {str(e)}")
            return Response({
                'status': 'error',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationCleanupAPIView(APIView):
    """
    Trigger cleanup of old notifications.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Trigger notification cleanup"""
        # Only allow staff users to trigger cleanup
        if not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to trigger cleanup'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from .websocket_utils import cleanup_old_notifications
            
            max_age_hours = request.data.get('max_age_hours', 24)
            
            # Validate max_age_hours
            if not isinstance(max_age_hours, (int, float)) or max_age_hours <= 0:
                return Response(
                    {'error': 'max_age_hours must be a positive number'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cleaned_count = cleanup_old_notifications(max_age_hours)
            
            return Response({
                'success': True,
                'message': f'Cleaned up {cleaned_count} old notifications',
                'cleaned_count': cleaned_count,
                'max_age_hours': max_age_hours,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to cleanup notifications: {str(e)}")
            return Response(
                {'error': f'Cleanup failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkNotificationAPIView(APIView):
    """
    Send bulk notifications to multiple channels.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Send bulk notifications"""
        # Only allow staff users to send bulk notifications
        if not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to send bulk notifications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from .websocket_utils import EnhancedWebSocketNotificationManager
            
            # Get notification data
            message_data = request.data.get('message', {})
            target_type = request.data.get('target_type', 'global')  # 'global', 'portal', 'event', 'user'
            targets = request.data.get('targets', [])
            
            if not message_data or 'event' not in message_data:
                return Response(
                    {'error': 'Message data with event type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            sent_count = 0
            
            if target_type == 'global':
                # Send to global channel
                EnhancedWebSocketNotificationManager.broadcast_system_notification(message_data)
                sent_count = 1
                
            elif target_type == 'portal':
                # Send to portal channels
                valid_portals = ['staff', 'participant', 'organizer']
                for portal in targets:
                    if portal in valid_portals:
                        EnhancedWebSocketNotificationManager.send_portal_notification(portal, message_data)
                        sent_count += 1
                        
            elif target_type == 'event':
                # Send to event channels
                from .websocket_utils import WebSocketNotificationManager
                for event_id in targets:
                    try:
                        event_channel = WebSocketNotificationManager.get_event_channel_name(event_id)
                        WebSocketNotificationManager.store_notification(event_channel, message_data)
                        sent_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to send notification to event {event_id}: {str(e)}")
                        
            elif target_type == 'user':
                # Send to user channels
                from .websocket_utils import WebSocketNotificationManager
                for user_id in targets:
                    try:
                        user_channel = WebSocketNotificationManager.get_user_channel_name(user_id)
                        WebSocketNotificationManager.store_notification(user_channel, message_data)
                        sent_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to send notification to user {user_id}: {str(e)}")
            
            else:
                return Response(
                    {'error': f'Invalid target_type: {target_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'message': f'Sent {sent_count} bulk notifications',
                'sent_count': sent_count,
                'target_type': target_type,
                'targets': targets,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send bulk notifications: {str(e)}")
            return Response(
                {'error': f'Bulk notification failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_test_notifications(request):
    """
    Trigger test notifications for development and testing.
    
    This endpoint allows testing of various notification types.
    """
    from django.conf import settings
    
    # Only allow in debug mode
    if not settings.DEBUG:
        return Response(
            {'error': 'This endpoint is only available in debug mode'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from .websocket_utils import (
            notify_color_extraction_progress,
            notify_theme_css_generated,
            notify_accessibility_validation_completed,
            notify_theme_variation_created,
            notify_bulk_operation_progress,
            notify_rate_limit_warning
        )
        
        test_type = request.data.get('test_type', 'all')
        event_id = request.data.get('event_id', 1)
        user_id = request.user.id
        
        notifications_sent = []
        
        if test_type in ['all', 'color_extraction']:
            notify_color_extraction_progress(event_id, 75, 'analyzing_colors', user_id)
            notifications_sent.append('color_extraction_progress')
        
        if test_type in ['all', 'css_generated']:
            notify_theme_css_generated(event_id, 1, 'staff', user_id)
            notifications_sent.append('theme_css_generated')
        
        if test_type in ['all', 'accessibility']:
            notify_accessibility_validation_completed(event_id, 1, True, ['brightness_adjusted'], user_id)
            notifications_sent.append('accessibility_validation_completed')
        
        if test_type in ['all', 'variation']:
            notify_theme_variation_created(event_id, 1, 1, 'dark', user_id)
            notifications_sent.append('theme_variation_created')
        
        if test_type in ['all', 'bulk_operation']:
            notify_bulk_operation_progress(event_id, 'variation_generation', 60, 3, 5, user_id)
            notifications_sent.append('bulk_operation_progress')
        
        if test_type in ['all', 'rate_limit']:
            notify_rate_limit_warning(user_id, 'theme_generation', 8, 10)
            notifications_sent.append('rate_limit_warning')
        
        return Response({
            'success': True,
            'message': f'Sent {len(notifications_sent)} test notifications',
            'notifications_sent': notifications_sent,
            'test_type': test_type,
            'event_id': event_id,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Failed to send test notifications: {str(e)}")
        return Response(
            {'error': f'Test notifications failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )