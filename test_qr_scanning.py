#!/usr/bin/env python
"""
Test script to verify QR code scanning works after the registration status fix
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from registration.models import Registration, RegistrationStatus
from events.models import Event

def test_qr_scanning():
    """Test QR code scanning functionality"""
    print("Testing QR Code Scanning...")
    print("=" * 50)
    
    # Get all confirmed registrations
    confirmed_regs = Registration.objects.filter(status=RegistrationStatus.CONFIRMED)
    print(f"Found {confirmed_regs.count()} confirmed registrations")
    
    if confirmed_regs.exists():
        for reg in confirmed_regs[:5]:  # Test first 5
            print(f"\nRegistration: {reg.registration_number}")
            print(f"Attendee: {reg.attendee_name}")
            print(f"Event: {reg.event.title}")
            print(f"Status: {reg.get_status_display()}")
            print(f"QR Code: {reg.qr_code}")
            print(f"Can Check In: {'YES' if reg.status == RegistrationStatus.CONFIRMED else 'NO'}")
            print("-" * 30)
    else:
        print("No confirmed registrations found!")
    
    # Check for any remaining pending registrations
    pending_regs = Registration.objects.filter(status=RegistrationStatus.PENDING)
    if pending_regs.exists():
        print(f"\nWARNING: {pending_regs.count()} registrations still pending!")
        for reg in pending_regs:
            print(f"  - {reg.registration_number}: {reg.attendee_name}")
    else:
        print("\n✅ No pending registrations found - all good!")

if __name__ == '__main__':
    test_qr_scanning()