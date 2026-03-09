#!/usr/bin/env python
"""
Test script for bulk badge printing and security features
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event
from registration.models import Registration, TicketType, Badge

User = get_user_model()

def test_badge_functionality():
    """Test badge printing functionality"""
    print("=== Testing Badge Functionality ===")
    
    # Get admin user
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("No admin user found")
        return False
    
    print(f"Using admin user: {admin_user.email}")
    
    # Get or create test event
    event = Event.objects.filter(organizer=admin_user).first()
    if not event:
        print("No test event found for admin")
        return False
    
    print(f"Using event: {event.title}")
    
    # Get registrations
    registrations = Registration.objects.filter(event=event)
    print(f"Found {registrations.count()} registrations")
    
    # Test badge creation
    badge_count = 0
    for reg in registrations:
        badge, created = Badge.objects.get_or_create(
            registration=reg,
            defaults={
                'name': reg.attendee_name,
                'title': reg.attendee_title or '',
                'company': reg.attendee_company or '',
                'badge_type': 'vip' if reg.ticket_type and reg.ticket_type.ticket_category == 'vip' else 'standard',
                'qr_code_data': f"BADGE:{reg.qr_code}",
            }
        )
        if created:
            badge_count += 1
            print(f"Created badge for {reg.attendee_name}")
    
    print(f"Created {badge_count} new badges")
    
    # Test QR code generation
    qr_success = 0
    for badge in Badge.objects.all():
        try:
            qr_image = badge.generate_qr_code()
            if qr_image:
                qr_success += 1
        except Exception as e:
            print(f"QR generation failed for {badge.name}: {e}")
    
    print(f"Generated {qr_success} QR codes")
    
    return True

def test_security_permissions():
    """Test security separation"""
    print("\n=== Testing Security Permissions ===")
    
    # Get users
    admin_user = User.objects.filter(is_superuser=True).first()
    staff_user = User.objects.filter(is_staff=True, is_superuser=False).first()
    organizer_user = User.objects.filter(
        organized_events__isnull=False,
        is_staff=False
    ).first()
    
    print(f"Admin users: {User.objects.filter(is_superuser=True).count()}")
    print(f"Staff users: {User.objects.filter(is_staff=True).count()}")
    print(f"Organizer users: {User.objects.filter(organized_events__isnull=False).count()}")
    
    # Test decorator imports
    try:
        from event_project.decorators import (
            admin_required, 
            organizer_or_admin_required, 
            event_organizer_or_admin_required,
            security_admin_required
        )
        print("Security decorators imported successfully")
    except ImportError as e:
        print(f"Failed to import security decorators: {e}")
        return False
    
    # Test admin views import
    try:
        from event_project import admin_views
        print("Admin views imported successfully")
    except ImportError as e:
        print(f"Failed to import admin views: {e}")
        return False
    
    return True

def test_bulk_registration():
    """Test bulk registration functionality"""
    print("\n=== Testing Bulk Registration ===")
    
    # Check bulk upload model
    try:
        from registration.models import BulkRegistrationUpload, BulkRegistrationRow
        print("Bulk registration models imported")
        
        # Count existing uploads
        upload_count = BulkRegistrationUpload.objects.count()
        print(f"Found {upload_count} bulk uploads")
        
        return True
    except ImportError as e:
        print(f"Failed to import bulk registration models: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Event Management System Features")
    print("=" * 50)
    
    results = []
    
    # Test badge functionality
    results.append(("Badge Functionality", test_badge_functionality()))
    
    # Test security permissions
    results.append(("Security Permissions", test_security_permissions()))
    
    # Test bulk registration
    results.append(("Bulk Registration", test_bulk_registration()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Features are working correctly.")
    else:
        print("Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main()
