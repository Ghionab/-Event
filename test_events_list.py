#!/usr/bin/env python
"""
Test staff events list functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_staff')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from events.models import Event
from registration.models import Registration

User = get_user_model()

def test_events_list():
    # Create a test client
    client = Client()
    
    # Get or create a staff user
    staff_user, created = User.objects.get_or_create(
        email='staff_test@example.com',
        defaults={
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'Staff',
            'role': 'staff'
        }
    )
    
    if created:
        staff_user.set_password('testpass123')
        staff_user.save()
    
    print(f"Using staff user: {staff_user.email}")
    
    # Login as staff
    client.force_login(staff_user)
    
    # Test the events list page
    response = client.get('/staff/events/')
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Check if events are displayed
        events_with_registrations = Event.objects.filter(registrations__isnull=False).distinct()
        print(f"Expected events with registrations: {events_with_registrations.count()}")
        
        for event in events_with_registrations:
            if event.title in content:
                print(f"✓ Found: {event.title}")
            else:
                print(f"✗ Missing: {event.title}")
        
        # Check for key elements
        if 'Gate Staff Portal' in content:
            print("✓ Portal title found")
        else:
            print("✗ Portal title not found")
            
        if 'Events' in content or 'events' in content:
            print("✓ Events section found")
        else:
            print("✗ Events section not found")
            
    else:
        print(f"✗ Failed to load page: {response.status_code}")
        print(response.content.decode('utf-8'))

if __name__ == '__main__':
    test_events_list()
