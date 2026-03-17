"""
WebSocket consumers for real-time calendar updates
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Registration, AttendeePreference, EventSession


class CalendarConsumer(AsyncWebsocketConsumer):
    """Consumer for real-time calendar updates"""
    
    async def connect(self):
        """Accept connection and authenticate user"""
        self.user = self.scope["user"]
        
        # Only allow authenticated users
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        # Create personal group for this user
        self.user_group_name = f"calendar_{self.user.id}"
        
        # Join personal group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Leave user group when disconnecting"""
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to keep-alive
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif message_type == 'subscribe_events':
                # Subscribe to specific event updates
                event_ids = data.get('event_ids', [])
                for event_id in event_ids:
                    event_group_name = f"event_{event_id}"
                    await self.channel_layer.group_add(
                        event_group_name,
                        self.channel_name
                    )
                    
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def calendar_update(self, event):
        """Send calendar update to user"""
        await self.send(text_data=json.dumps(event))
    
    async def session_added(self, event):
        """Handle session added notification"""
        await self.send(text_data=json.dumps({
            'type': 'session_added',
            'event': event['event']
        }))
    
    async def session_removed(self, event):
        """Handle session removed notification"""
        await self.send(text_data=json.dumps({
            'type': 'session_removed',
            'event_id': event['event_id']
        }))
    
    async def session_updated(self, event):
        """Handle session updated notification"""
        await self.send(text_data=json.dumps({
            'type': 'session_updated',
            'event': event['event']
        }))
    
    async def event_cancelled(self, event):
        """Handle event cancelled notification"""
        await self.send(text_data=json.dumps({
            'type': 'event_cancelled',
            'event_id': event['event_id']
        }))


class EventUpdateConsumer(AsyncWebsocketConsumer):
    """Consumer for event-specific updates"""
    
    async def connect(self):
        """Accept connection for event updates"""
        self.user = self.scope["user"]
        
        # Only allow authenticated users
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        # Get event ID from URL
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.event_group_name = f"event_{self.event_id}"
        
        # Check if user is registered for this event
        is_registered = await self.check_user_registered(self.event_id)
        if not is_registered:
            await self.close()
            return
        
        # Join event group
        await self.channel_layer.group_add(
            self.event_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Leave event group when disconnecting"""
        await self.channel_layer.group_discard(
            self.event_group_name,
            self.channel_name
        )
    
    @database_sync_to_async
    def check_user_registered(self, event_id):
        """Check if user is registered for the event"""
        from .models import Registration, RegistrationStatus
        from django.db import models
        
        return Registration.objects.filter(
            models.Q(user=self.user) | models.Q(attendee_email__iexact=self.user.email),
            event_id=event_id,
            status__in=[
                RegistrationStatus.PENDING,
                RegistrationStatus.CONFIRMED,
                RegistrationStatus.CHECKED_IN
            ]
        ).exists()
    
    async def event_update(self, event):
        """Send event update to connected users"""
        await self.send(text_data=json.dumps(event))
    
    async def session_schedule_change(self, event):
        """Handle session schedule changes"""
        await self.send(text_data=json.dumps({
            'type': 'session_schedule_change',
            'event': event['event']
        }))


@database_sync_to_async
def get_user_calendar_events(user_id):
    """Get user's calendar events for WebSocket context"""
    from django.utils import timezone
    from django.db import models
    
    user_registrations = Registration.objects.filter(
        models.Q(user_id=user_id) | models.Q(attendee_email__iexact=user.email),
        event__start_date__gte=timezone.now(),
        status__in=['confirmed', 'checked_in']
    ).select_related('event')
    
    events = []
    for reg in user_registrations:
        events.append({
            'id': f"event_{reg.event.id}",
            'title': reg.event.title,
            'start': reg.event.start_date.isoformat(),
            'end': reg.event.end_date.isoformat(),
            'type': 'registered'
        })
        
        # Add saved sessions
        prefs = AttendeePreference.objects.filter(user_id=user_id, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions,
                event=reg.event
            ).select_related('event')
            
            for session in sessions:
                events.append({
                    'id': f"session_{session.id}",
                    'title': session.title,
                    'start': session.start_time.isoformat(),
                    'end': session.end_time.isoformat(),
                    'type': 'saved'
                })
    
    return events
