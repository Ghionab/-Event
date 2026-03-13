#!/usr/bin/env python
"""
Test script to verify the template fix for bulk registration
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from events.models import Event
from registration.models import TicketType

User = get_user_model()

def test_bulk_registration_access():
    """Test that bulk registration pages load without template errors"""
    
    print("=== Testing Bulk Registration Template Fix ===")
    
    # Create test client
    client = Client()
    
    # Create test user and login
    user = User.objects.filter(email='organizer@test.com').first()
    if not user:
        user = User.objects.create_user(
            email='organizer@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
    
    # Login
    client.login(email='organizer@test.com', password='testpass123')
    
    # Get or create test event
    event = Event.objects.filter(title='Test Event').first()
    if not event:
        from datetime import datetime, timezone
        event = Event.objects.create(
            title='Test Event',
            description='Test event for bulk registration',
            organizer=user,
            start_date=datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc),
            end_date=datetime(2026, 4, 1, 18, 0, tzinfo=timezone.utc),
            venue_name='Test Location',
            max_attendees=1000
        )
    
    # Create ticket type
    ticket_type, created = TicketType.objects.get_or_create(
        event=event,
        name='General Admission',
        defaults={
            'price': 50.00,
            'quantity_available': 500,
            'is_active': True
        }
    )
    
    print(f"✓ Test event: {event.title}")
    print(f"✓ Test ticket type: {ticket_type.name}")
    
    # Test bulk registration start page
    try:
        url = reverse('registration:bulk_wizard_start', args=[event.id])
        response = client.get(url)
        if response.status_code == 200:
            print("✓ Bulk registration start page loads successfully")
        else:
            print(f"✗ Bulk registration start page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error accessing bulk registration: {e}")
        return False
    
    print("\n🎉 Template fix verification completed successfully!")
    return True

if __name__ == '__main__':
    success = test_bulk_registration_access()
    sys.exit(0 if success else 1)