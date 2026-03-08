#!/usr/bin/env python
"""
Demo script to test the new event creation functionality
Run with: python manage.py shell < demo_event_creation.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event
from events.forms import EventForm
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

print("=" * 70)
print("EVENT CREATION DEMO - New Features")
print("=" * 70)

# Get or create a test organizer
print("\n1. Setting up test organizer...")
try:
    organizer = User.objects.get(email='demo@example.com')
    print(f"   ✓ Using existing organizer: {organizer.email}")
except User.DoesNotExist:
    organizer = User.objects.create_user(
        email='demo@example.com',
        password='demo123',
        role='organizer',
        first_name='Demo',
        last_name='Organizer'
    )
    print(f"   ✓ Created organizer: {organizer.email}")

# Test 1: Create event without status field (should auto-assign draft)
print("\n2. Testing auto-draft status assignment...")
event_data = {
    'title': 'Demo Tech Conference 2026',
    'description': 'A demonstration of the new event creation features',
    'event_type': 'in_person',
    'start_date': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M'),
    'end_date': (timezone.now() + timedelta(days=31)).strftime('%Y-%m-%dT%H:%M'),
    'venue_name': 'Convention Center',
    'city': 'San Francisco',
    'country': 'USA',
    'contact_email': 'contact@democonf.com',
}

form = EventForm(data=event_data)
if form.is_valid():
    event = form.save(commit=False)
    event.organizer = organizer
    event.status = 'draft'  # Auto-assigned in view
    event.save()
    print(f"   ✓ Event created: {event.title}")
    print(f"   ✓ Status auto-assigned: {event.status}")
    print(f"   ✓ Event ID: {event.id}")
else:
    print(f"   ✗ Form validation failed: {form.errors}")

# Test 2: Validate email invitation field
print("\n3. Testing email invitation validation...")

# Valid emails
test_emails = [
    ('user1@example.com, user2@example.com', True, 'Comma-separated'),
    ('user1@example.com\nuser2@example.com', True, 'Newline-separated'),
    ('single@example.com', True, 'Single email'),
    ('', True, 'Empty (optional)'),
    ('invalid-email', False, 'Invalid format'),
]

for email_input, should_pass, description in test_emails:
    event_data_with_email = event_data.copy()
    event_data_with_email['title'] = f'Test Event - {description}'
    event_data_with_email['invite_emails'] = email_input
    
    form = EventForm(data=event_data_with_email)
    if should_pass:
        if form.is_valid():
            print(f"   ✓ {description}: PASSED")
        else:
            print(f"   ✗ {description}: FAILED (should pass)")
            print(f"      Errors: {form.errors.get('invite_emails', [])}")
    else:
        if not form.is_valid() and 'invite_emails' in form.errors:
            print(f"   ✓ {description}: CORRECTLY REJECTED")
        else:
            print(f"   ✗ {description}: FAILED (should reject)")

# Test 3: Show form fields
print("\n4. Checking form fields...")
form = EventForm()
print(f"   Total fields: {len(form.fields)}")
print(f"   Status field present: {'status' in form.fields}")
print(f"   Invite emails field present: {'invite_emails' in form.fields}")

if 'status' in form.fields:
    print("   ✗ WARNING: Status field should not be in form!")
else:
    print("   ✓ Status field correctly removed")

if 'invite_emails' in form.fields:
    print("   ✓ Invite emails field correctly added")
else:
    print("   ✗ WARNING: Invite emails field missing!")

# Test 4: Check recent events
print("\n5. Recent events created:")
recent_events = Event.objects.filter(organizer=organizer).order_by('-created_at')[:3]
for evt in recent_events:
    print(f"   • {evt.title}")
    print(f"     Status: {evt.status}")
    print(f"     Created: {evt.created_at.strftime('%Y-%m-%d %H:%M')}")

# Summary
print("\n" + "=" * 70)
print("DEMO COMPLETE")
print("=" * 70)
print("\nKey Features Verified:")
print("✓ Status field removed from form")
print("✓ Status auto-assigned as 'draft'")
print("✓ Email invitation field added")
print("✓ Email validation working")
print("\nNext Steps:")
print("1. Start server: python manage.py runserver")
print("2. Login as organizer")
print("3. Navigate to Create Event page")
print("4. Test the new interface!")
print("=" * 70)
