#!/usr/bin/env python
"""
Test script to verify Gate Staff Portal setup
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from users.models import User, UserRole
from events.models import Event
from registration.models import Registration, TicketType
from django.utils import timezone
from datetime import timedelta

def test_staff_portal():
    print("=" * 60)
    print("Gate Staff Portal - Setup Verification")
    print("=" * 60)
    
    # Test 1: Check if STAFF role exists
    print("\n✓ Test 1: Checking STAFF role...")
    try:
        assert 'staff' in [choice[0] for choice in UserRole.choices]
        print("  ✓ STAFF role exists in UserRole choices")
    except AssertionError:
        print("  ✗ STAFF role not found!")
        return False
    
    # Test 2: Check staff users
    print("\n✓ Test 2: Checking staff users...")
    staff_users = User.objects.filter(role='staff')
    if staff_users.exists():
        print(f"  ✓ Found {staff_users.count()} staff user(s):")
        for user in staff_users:
            print(f"    - {user.email}")
    else:
        print("  ⚠ No staff users found. Creating test staff user...")
        try:
            staff = User.objects.create_user(
                email='staff@test.com',
                password='stafftest123',
                first_name='Test',
                last_name='Staff',
                role='staff'
            )
            print(f"  ✓ Created test staff user: {staff.email}")
            print(f"    Password: stafftest123")
        except Exception as e:
            print(f"  ✗ Error creating staff user: {e}")
            return False
    
    # Test 3: Check for active events
    print("\n✓ Test 3: Checking active events...")
    today = timezone.now().date()
    active_events = Event.objects.filter(start_date__gte=today)
    if active_events.exists():
        print(f"  ✓ Found {active_events.count()} active event(s):")
        for event in active_events[:3]:
            print(f"    - {event.title} ({event.start_date})")
    else:
        print("  ⚠ No active events found. Creating test event...")
        try:
            organizer = User.objects.filter(role='organizer').first()
            if not organizer:
                organizer = User.objects.create_user(
                    email='organizer@test.com',
                    password='orgtest123',
                    first_name='Test',
                    last_name='Organizer',
                    role='organizer'
                )
                print(f"  ✓ Created test organizer: {organizer.email}")
            
            event = Event.objects.create(
                title="Test Event for Staff Portal",
                description="Test event",
                start_date=today,
                end_date=today + timedelta(days=1),
                venue_name="Test Venue",
                organizer=organizer,
                status='published'
            )
            print(f"  ✓ Created test event: {event.title}")
            
            # Create ticket type
            ticket = TicketType.objects.create(
                event=event,
                name="General Admission",
                price=0,
                quantity_available=50,
                sales_start=timezone.now() - timedelta(days=7),
                sales_end=timezone.now() + timedelta(days=1)
            )
            print(f"  ✓ Created ticket type: {ticket.name}")
            
            # Create sample registrations
            for i in range(1, 6):
                Registration.objects.create(
                    event=event,
                    ticket_type=ticket,
                    attendee_name=f"Test Attendee {i}",
                    attendee_email=f"attendee{i}@test.com",
                    status='confirmed',
                    total_amount=0
                )
            print(f"  ✓ Created 5 test registrations")
            
        except Exception as e:
            print(f"  ✗ Error creating test data: {e}")
            return False
    
    # Test 4: Check registrations
    print("\n✓ Test 4: Checking registrations...")
    total_regs = Registration.objects.count()
    confirmed_regs = Registration.objects.filter(status='confirmed').count()
    checked_in_regs = Registration.objects.filter(status='checked_in').count()
    print(f"  ✓ Total registrations: {total_regs}")
    print(f"  ✓ Confirmed: {confirmed_regs}")
    print(f"  ✓ Checked in: {checked_in_regs}")
    
    # Test 5: Check staff app
    print("\n✓ Test 5: Checking staff app...")
    try:
        from staff import views, decorators, urls
        print("  ✓ Staff app modules imported successfully")
    except ImportError as e:
        print(f"  ✗ Error importing staff app: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Run the staff portal:")
    print("   python run_staff_portal.py")
    print("\n2. Access the portal:")
    print("   http://localhost:8002")
    print("\n3. Login with staff credentials:")
    if User.objects.filter(email='staff@test.com').exists():
        print("   Email: staff@test.com")
        print("   Password: stafftest123")
    else:
        staff = User.objects.filter(role='staff').first()
        if staff:
            print(f"   Email: {staff.email}")
            print("   Password: (your password)")
    
    print("\n4. Also run other portals:")
    print("   Terminal 1: python manage.py runserver 8000")
    print("   Terminal 2: python manage.py runserver 8001 --settings=event_project.settings_participant")
    print("   Terminal 3: python run_staff_portal.py")
    
    return True

if __name__ == '__main__':
    try:
        success = test_staff_portal()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
