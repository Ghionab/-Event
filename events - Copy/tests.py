from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone
from .models import Event, EventSession, EventType, EventStatus, Speaker, Track, Room, Sponsor

User = get_user_model()


class EventModelTest(TestCase):
    """Tests for Event model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='organizer'
        )
    
    def test_create_event(self):
        """Test creating an event"""
        event = Event.objects.create(
            title='Test Event',
            description='A test event description',
            event_type=EventType.IN_PERSON,
            status=EventStatus.DRAFT,
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            venue_name='Test Venue',
            address='123 Test St',
            city='Test City',
            country='Test Country',
            organizer=self.user
        )
        self.assertEqual(event.title, 'Test Event')
        self.assertEqual(event.slug, 'test-event')
        self.assertEqual(str(event), 'Test Event')
    
    def test_event_auto_slug(self):
        """Test automatic slug generation"""
        event = Event.objects.create(
            title='My Test Event!',
            description='Description',
            event_type=EventType.VIRTUAL,
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
        self.assertEqual(event.slug, 'my-test-event')
    
    def test_event_ordering(self):
        """Test event ordering by start_date descending"""
        event1 = Event.objects.create(
            title='Event 1',
            description='Desc',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=11),
            organizer=self.user
        )
        event2 = Event.objects.create(
            title='Event 2',
            description='Desc',
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now() + timedelta(days=6),
            organizer=self.user
        )
        events = list(Event.objects.all())
        self.assertEqual(events[0], event1)
        self.assertEqual(events[1], event2)


class EventSessionModelTest(TestCase):
    """Tests for EventSession model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_create_session(self):
        """Test creating an event session"""
        session = EventSession.objects.create(
            event=self.event,
            title='Test Session',
            description='A test session',
            start_time=timezone.now() + timedelta(days=7, hours=10),
            end_time=timezone.now() + timedelta(days=7, hours=11),
            location='Room A'
        )
        self.assertEqual(session.title, 'Test Session')
        self.assertEqual(str(session), 'Test Session')
    
    def test_session_ordering(self):
        """Test sessions are ordered by start_time"""
        session1 = EventSession.objects.create(
            event=self.event,
            title='Session 1',
            start_time=timezone.now() + timedelta(days=7, hours=14),
            end_time=timezone.now() + timedelta(days=7, hours=15)
        )
        session2 = EventSession.objects.create(
            event=self.event,
            title='Session 2',
            start_time=timezone.now() + timedelta(days=7, hours=10),
            end_time=timezone.now() + timedelta(days=7, hours=11)
        )
        sessions = list(EventSession.objects.all())
        self.assertEqual(sessions[0], session2)
        self.assertEqual(sessions[1], session1)


class EventViewsTest(TestCase):
    """Tests for Event views"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='organizer'
        )
        self.event = Event.objects.create(
            title='Public Event',
            description='A public event',
            status=EventStatus.PUBLISHED,
            is_public=True,
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_home_view(self):
        """Test home page shows published events"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Event')
    
    def test_event_list_view(self):
        """Test event list page"""
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Event')
    
    def test_event_detail_view(self):
        """Test event detail page"""
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Event')
    
    def test_event_create_requires_login(self):
        """Test that event creation requires authentication"""
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_event_create_authenticated(self):
        """Test event creation for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_event_create_auto_draft_status(self):
        """Test that new events are automatically set to draft status"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.post(reverse('event_create'), {
            'title': 'New Event',
            'description': 'Test description',
            'event_type': 'in_person',
            'start_date': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'end_date': (timezone.now() + timedelta(days=8)).strftime('%Y-%m-%dT%H:%M'),
            'venue_name': 'Test Venue',
            'city': 'Test City',
            'country': 'Test Country',
        })
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check that event was created with draft status
        event = Event.objects.get(title='New Event')
        self.assertEqual(event.status, 'draft')
        self.assertEqual(event.organizer, self.user)
    
    def test_event_create_with_email_invitations(self):
        """Test event creation with email invitations"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.post(reverse('event_create'), {
            'title': 'Event with Invites',
            'description': 'Test description',
            'event_type': 'in_person',
            'start_date': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'end_date': (timezone.now() + timedelta(days=8)).strftime('%Y-%m-%dT%H:%M'),
            'venue_name': 'Test Venue',
            'city': 'Test City',
            'country': 'Test Country',
            'invite_emails': 'guest1@example.com, guest2@example.com',
        })
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check that event was created
        event = Event.objects.get(title='Event with Invites')
        self.assertEqual(event.status, 'draft')
    
    def test_event_edit_requires_permission(self):
        """Test event edit requires owner or staff"""
        # Not logged in
        response = self.client.get(reverse('event_edit', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        
        # Logged in as non-owner
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(email='other@example.com', password='otherpass123')
        response = self.client.get(reverse('event_edit', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_event_edit_owner(self):
        """Test event edit for owner"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('event_edit', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_event_delete_requires_permission(self):
        """Test event delete requires owner or staff"""
        # Not logged in
        response = self.client.get(reverse('event_delete', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        
        # Logged in as non-owner
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(email='other@example.com', password='otherpass123')
        response = self.client.get(reverse('event_delete', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_event_delete_owner(self):
        """Test event delete for owner"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('event_delete', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_session_list_requires_login(self):
        """Test session list requires authentication"""
        response = self.client.get(reverse('session_list', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_session_create_requires_login(self):
        """Test session creation requires authentication"""
        response = self.client.get(reverse('session_create', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)


# Phase 3 Tests - Content & Agenda

class SpeakerModelTest(TestCase):
    """Tests for Speaker model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_create_speaker(self):
        """Test creating a speaker"""
        speaker = Speaker.objects.create(
            event=self.event,
            name='John Doe',
            email='john@example.com',
            job_title='CEO',
            company='Tech Corp',
            bio='Experienced speaker',
            is_confirmed=True
        )
        self.assertEqual(speaker.name, 'John Doe')
        self.assertTrue(speaker.is_confirmed)
        self.assertEqual(str(speaker), 'John Doe')
    
    def test_speaker_social_links(self):
        """Test speaker social links"""
        speaker = Speaker.objects.create(
            event=self.event,
            name='Jane Doe',
            twitter='janedoe',
            linkedin='https://linkedin.com/in/janedoe'
        )
        links = speaker.get_full_social_links()
        self.assertEqual(links['twitter'], 'janedoe')
        self.assertEqual(links['linkedin'], 'https://linkedin.com/in/janedoe')


class TrackModelTest(TestCase):
    """Tests for Track model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_create_track(self):
        """Test creating a track"""
        track = Track.objects.create(
            event=self.event,
            name='Technical',
            description='Technical sessions',
            color='#007bff',
            order=1
        )
        self.assertEqual(track.name, 'Technical')
        self.assertEqual(track.color, '#007bff')
        self.assertEqual(str(track), 'Test Event - Technical')


class RoomModelTest(TestCase):
    """Tests for Room model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_create_room(self):
        """Test creating a room"""
        room = Room.objects.create(
            event=self.event,
            name='Main Hall',
            capacity=500,
            building='Convention Center',
            floor='1st Floor'
        )
        self.assertEqual(room.name, 'Main Hall')
        self.assertEqual(room.capacity, 500)
        self.assertEqual(str(room), 'Main Hall')


class SponsorModelTest(TestCase):
    """Tests for Sponsor model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_create_sponsor(self):
        """Test creating a sponsor"""
        sponsor = Sponsor.objects.create(
            event=self.event,
            company_name='Tech Corp',
            tier='gold',
            website='https://techcorp.com',
            contact_name='John Smith',
            contact_email='john@techcorp.com'
        )
        self.assertEqual(sponsor.company_name, 'Tech Corp')
        self.assertEqual(sponsor.tier, 'gold')
        self.assertEqual(str(sponsor), 'Tech Corp')


class SessionModelTest(TestCase):
    """Tests for enhanced EventSession model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
        self.track = Track.objects.create(
            event=self.event,
            name='Technical',
            color='#007bff'
        )
    
    def test_session_duration(self):
        """Test session duration calculation"""
        session = EventSession.objects.create(
            event=self.event,
            title='Test Session',
            start_time=timezone.now() + timedelta(days=7, hours=10),
            end_time=timezone.now() + timedelta(days=7, hours=11, minutes=30),
            track=self.track
        )
        self.assertEqual(session.duration, 90)  # 90 minutes
    
    def test_session_is_full(self):
        """Test session capacity check"""
        session = EventSession.objects.create(
            event=self.event,
            title='Full Session',
            start_time=timezone.now() + timedelta(days=7, hours=10),
            end_time=timezone.now() + timedelta(days=7, hours=11),
            capacity=10,
            registered_count=10
        )
        self.assertTrue(session.is_full)
        self.assertEqual(session.available_spots, 0)
    
    def test_session_available_spots(self):
        """Test available spots calculation"""
        session = EventSession.objects.create(
            event=self.event,
            title='Available Session',
            start_time=timezone.now() + timedelta(days=7, hours=10),
            end_time=timezone.now() + timedelta(days=7, hours=11),
            capacity=50,
            registered_count=30
        )
        self.assertFalse(session.is_full)
        self.assertEqual(session.available_spots, 20)


class ExportViewsTest(TestCase):
    """Tests for export views"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
        EventSession.objects.create(
            event=self.event,
            title='Session 1',
            start_time=timezone.now() + timedelta(days=7, hours=10),
            end_time=timezone.now() + timedelta(days=7, hours=11)
        )
    
    def test_export_agenda_requires_login(self):
        """Test agenda export requires login"""
        response = self.client.get(reverse('export_agenda', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_export_agenda_authenticated(self):
        """Test agenda export for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('export_agenda', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'text/csv')
    
    def test_export_speakers_requires_login(self):
        """Test speakers export requires login"""
        response = self.client.get(reverse('export_speakers', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_export_speakers_authenticated(self):
        """Test speakers export for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('export_speakers', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'text/csv')


class SpeakerViewsTest(TestCase):
    """Tests for speaker views"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
        self.speaker = Speaker.objects.create(
            event=self.event,
            name='John Doe',
            email='john@example.com'
        )
    
    def test_speaker_list_requires_login(self):
        """Test speaker list requires login"""
        response = self.client.get(reverse('speaker_list', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_speaker_list_authenticated(self):
        """Test speaker list for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('speaker_list', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
    
    def test_speaker_create_requires_login(self):
        """Test speaker creation requires login"""
        response = self.client.get(reverse('speaker_create', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_speaker_create_authenticated(self):
        """Test speaker creation for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('speaker_create', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
