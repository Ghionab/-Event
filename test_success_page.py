#!/usr/bin/env python
"""Test registration success page"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_participant')
django.setup()

from registration.models import Registration

def test_success_page():
    """Test registration success page"""
    
    # Get a recent registration
    registration = Registration.objects.order_by('-created_at').first()
    
    if registration:
        print(f"Found registration: {registration.registration_number}")
        print(f"Event: {registration.event.title}")
        print(f"Attendee: {registration.attendee_name}")
        print(f"Success URL: http://localhost:8001/registration/success/{registration.id}/")
        
        # Test QR code generation
        try:
            qr_image = registration.generate_qr_code_image()
            if qr_image:
                print("QR code generation: SUCCESS")
            else:
                print("QR code generation: FAILED")
        except Exception as e:
            print(f"QR code generation error: {e}")
    else:
        print("No registrations found")

if __name__ == "__main__":
    test_success_page()
