"""
External calendar synchronization utilities
"""
import json
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Registration, AttendeePreference, SessionAttendance
from events.models import Event, EventSession


class GoogleCalendarSync:
    """Google Calendar synchronization"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://www.googleapis.com/calendar/v3'
    
    def export_events(self, user, calendar_id='primary'):
        """Export user's event schedule to Google Calendar"""
        try:
            # Get user's events
            events = self._get_user_events(user)
            
            exported_count = 0
            for event_data in events:
                google_event = self._format_for_google(event_data)
                response = requests.post(
                    f'{self.base_url}/calendars/{calendar_id}/events',
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    },
                    json=google_event
                )
                
                if response.status_code == 200:
                    exported_count += 1
            
            return {
                'success': True,
                'exported_count': exported_count,
                'message': f'Successfully exported {exported_count} events to Google Calendar'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to export to Google Calendar'
            }
    
    def import_events(self, user, calendar_id='primary'):
        """Import events from Google Calendar"""
        try:
            # Get events from Google Calendar
            now = timezone.now()
            time_min = now.isoformat()
            time_max = (now + timedelta(days=365)).isoformat()
            
            response = requests.get(
                f'{self.base_url}/calendars/{calendar_id}/events',
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                },
                params={
                    'timeMin': time_min,
                    'timeMax': time_max,
                    'singleEvents': True,
                    'orderBy': 'startTime'
                }
            )
            
            if response.status_code == 200:
                google_events = response.json().get('items', [])
                imported_count = 0
                
                for google_event in google_events:
                    # Check if event matches our event pattern
                    if self._is_our_event(google_event):
                        imported_count += 1
                
                return {
                    'success': True,
                    'imported_count': imported_count,
                    'message': f'Found {imported_count} events from Google Calendar'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to fetch events from Google Calendar'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to import from Google Calendar'
            }
    
    def _get_user_events(self, user):
        """Get user's registered events and saved sessions"""
        from django.db import models
        from .models import RegistrationStatus
        
        now = timezone.now()
        events = []
        
        # Get registered events
        registrations = Registration.objects.filter(
            models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
            event__start_date__gte=now,
            status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
        ).select_related('event')
        
        for reg in registrations:
            events.append({
                'type': 'event',
                'title': reg.event.title,
                'start': reg.event.start_date,
                'end': reg.event.end_date,
                'description': reg.event.description,
                'location': reg.event.venue_name or 'Virtual',
                'event_id': reg.event.id
            })
            
            # Get saved sessions
            prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
            if prefs and prefs.saved_sessions:
                sessions = EventSession.objects.filter(
                    id__in=prefs.saved_sessions,
                    event=reg.event
                ).select_related('event').prefetch_related('speakers')
                
                for session in sessions:
                    speakers = ', '.join([s.name for s in session.speakers.all()])
                    events.append({
                        'type': 'session',
                        'title': session.title,
                        'start': session.start_time,
                        'end': session.end_time,
                        'description': f"{speakers}\n\n{session.description or ''}",
                        'location': session.location or reg.event.venue_name,
                        'event_id': reg.event.id,
                        'session_id': session.id
                    })
        
        return events
    
    def _format_for_google(self, event_data):
        """Format event data for Google Calendar API"""
        google_event = {
            'summary': event_data['title'],
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': event_data['start'].isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': event_data['end'].isoformat(),
                'timeZone': 'UTC'
            }
        }
        
        if event_data.get('location'):
            google_event['location'] = event_data['location']
        
        # Add extended properties to identify our events
        google_event['extendedProperties'] = {
            'private': {
                'eventhub_event_id': str(event_data['event_id']),
                'eventhub_type': event_data['type'],
                'eventhub_sync': 'true'
            }
        }
        
        return google_event
    
    def _is_our_event(self, google_event):
        """Check if Google Calendar event was created by our system"""
        extended_props = google_event.get('extendedProperties', {}).get('private', {})
        return extended_props.get('eventhub_sync') == 'true'


class OutlookCalendarSync:
    """Outlook Calendar synchronization"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://graph.microsoft.com/v1.0'
    
    def export_events(self, user):
        """Export user's event schedule to Outlook Calendar"""
        try:
            # Get user's events
            events = self._get_user_events(user)
            
            exported_count = 0
            for event_data in events:
                outlook_event = self._format_for_outlook(event_data)
                response = requests.post(
                    f'{self.base_url}/me/events',
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    },
                    json=outlook_event
                )
                
                if response.status_code == 201:
                    exported_count += 1
            
            return {
                'success': True,
                'exported_count': exported_count,
                'message': f'Successfully exported {exported_count} events to Outlook Calendar'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to export to Outlook Calendar'
            }
    
    def _get_user_events(self, user):
        """Get user's events (same as Google Calendar)"""
        # Reuse the same logic from GoogleCalendarSync
        google_sync = GoogleCalendarSync('')
        return google_sync._get_user_events(user)
    
    def _format_for_outlook(self, event_data):
        """Format event data for Outlook Calendar API"""
        outlook_event = {
            'subject': event_data['title'],
            'body': {
                'contentType': 'HTML',
                'content': event_data.get('description', '').replace('\n', '<br>')
            },
            'start': {
                'dateTime': event_data['start'].isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': event_data['end'].isoformat(),
                'timeZone': 'UTC'
            }
        }
        
        if event_data.get('location'):
            outlook_event['location'] = {
                'displayName': event_data['location']
            }
        
        # Add extensions to identify our events
        outlook_event['extensions'] = [{
            '@odata.type': '#microsoft.graph.openTypeExtension',
            'extensionName': 'eventhub.sync',
            'eventhub_event_id': str(event_data['event_id']),
            'eventhub_type': event_data['type'],
            'eventhub_sync': 'true'
        }]
        
        return outlook_event


def generate_ical_export(user):
    """Generate iCal export for user's schedule"""
    from icalendar import Calendar, Event
    from django.db import models
    from .models import RegistrationStatus
    
    cal = Calendar()
    cal.add('prodid', '-//EventHub//Event Schedule//EN')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')
    
    now = timezone.now()
    
    # Get registered events
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        event__start_date__gte=now,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')
    
    for reg in registrations:
        # Add event
        event = Event()
        event.add('summary', reg.event.title)
        event.add('description', reg.event.description)
        event.add('dtstart', reg.event.start_date)
        event.add('dtend', reg.event.end_date)
        event.add('location', reg.event.venue_name or 'Virtual')
        event.add('uid', f"event_{reg.event.id}@eventhub")
        event.add('status', 'CONFIRMED')
        cal.add_component(event)
        
        # Add saved sessions
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions,
                event=reg.event
            ).select_related('event').prefetch_related('speakers')
            
            for session in sessions:
                session_event = Event()
                speakers = ', '.join([s.name for s in session.speakers.all()])
                description = f"{speakers}\n\n{session.description or ''}" if speakers else session.description or ''
                
                session_event.add('summary', session.title)
                session_event.add('description', description)
                session_event.add('dtstart', session.start_time)
                session_event.add('dtend', session.end_time)
                session_event.add('location', session.location or reg.event.venue_name)
                session_event.add('uid', f"session_{session.id}@eventhub")
                session_event.add('status', 'CONFIRMED')
                cal.add_component(session_event)
    
    return cal.to_ical()


def get_calendar_sync_status(user):
    """Get calendar sync status for user"""
    # This would check if user has connected external calendars
    # For now, return placeholder status
    return {
        'google_connected': False,
        'outlook_connected': False,
        'last_sync': None,
        'sync_enabled': False
    }
