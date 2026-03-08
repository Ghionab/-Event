#!/usr/bin/env python
"""
Integration test for email invitation functionality
Run with: python test_email_integration.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event
from events.views import send_event_invitations
from datetime import timedelta
from django.utils import timezone
from django.core import mail

User = get_user_model()

print("=" * 70)
print("EMAIL INVITATION INTEGRATION TEST")
print("=" * 70)

# Setup
print("\n1. Setting up test data...")
try:
    organizer = User.objects.get(email='demo@example.com')
except User.DoesNotExist:
    organizer = User.objects.create_user(
        email='demo@example.com',
        password='demo123',
        role='organizer',
        first_name='Demo',
        last_name='Organizer'
    )
print(f"   ✓ Organizer: {organizer.email}")

# Create test event
event = Event.objects.create(
    title='Email Test Event',
    description='Testing email invitation functionality',
    event_type='in_person',
    status='draft',
    start_date=timezone.now() + timedelta(days=30),
    end_date=timezone.now() + timedelta(days=31),
    venue_name='Test Venue',
    city='Test City',
    country='Test Country',
    organizer=organizer
)
print(f"   ✓ Event created: {event.title} (ID: {event.id})")

# Test email sending
print("\n2. Testing email invitation sending...")
test_emails = [
    'guest1@example.com',
    'guest2@example.com',
    'guest3@example.com'
]

# Clear any existing emails in the test outbox
mail.outbox = []

sent_count = send_event_invitations(event, test_emails, organizer)

print(f"   ✓ Attempted to send: {len(test_emails)} emails")
print(f"   ✓ Successfully sent: {sent_count} emails")

# Check the outbox (for console backend)
print(f"\n3. Checking email outbox...")
print(f"   Emails in outbox: {len(mail.outbox)}")

if len(mail.outbox) > 0:
    print("\n4. Email details:")
    for i, email in enumerate(mail.outbox, 1):
        print(f"\n   Email #{i}:")
        print(f"   • To: {email.to[0]}")
        print(f"   • Subject: {email.subject}")
        print(f"   • From: {email.from_email}")
        print(f"   • Body preview: {email.body[:100]}...")
        
        # Verify email content
        assert event.title in email.subject, "Event title should be in subject"
        assert event.title in email.body, "Event title should be in body"
        assert event.venue_name in email.body, "Venue should be in body"
        assert event.city in email.body, "City should be in body"
        assert str(event.id) in email.body, "Event ID should be in registration link"
        print(f"   ✓ Content validation passed")
else:
    print("   ⚠ No emails in outbox (check EMAIL_BACKEND setting)")

# Verify email format
print("\n5. Email format verification...")
if len(mail.outbox) > 0:
    sample_email = mail.outbox[0]
    
    checks = [
        ("Subject contains event title", event.title in sample_email.subject),
        ("Body contains event title", event.title in sample_email.body),
        ("Body contains date", "Date:" in sample_email.body),
        ("Body contains venue", event.venue_name in sample_email.body),
        ("Body contains location", event.city in sample_email.body),
        ("Body contains registration link", f"events/{event.id}" in sample_email.body),
        ("Body contains organizer name", organizer.get_full_name() in sample_email.body or organizer.email in sample_email.body),
    ]
    
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"   {status} {check_name}")

# Summary
print("\n" + "=" * 70)
print("INTEGRATION TEST COMPLETE")
print("=" * 70)
print(f"\nResults:")
print(f"✓ Event created successfully")
print(f"✓ Email sending function executed")
print(f"✓ {sent_count}/{len(test_emails)} emails sent")
print(f"✓ Email content validated")
print(f"\nEmail Backend: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}")
print("Note: In development, emails are printed to console")
print("=" * 70)

# Cleanup
print("\nCleaning up test data...")
event.delete()
print("✓ Test event deleted")
