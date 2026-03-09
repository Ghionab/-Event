#!/usr/bin/env python
"""
Test script for QR code registration feature
Run with: python test_qr_registration.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from registration.models import Registration
from events.models import Event
from django.contrib.auth import get_user_model

User = get_user_model()


def test_qr_code_generation():
    """Test QR code generation for existing registrations"""
    print("=" * 60)
    print("Testing QR Code Generation")
    print("=" * 60)
    
    registrations = Registration.objects.all()[:5]
    
    if not registrations:
        print("❌ No registrations found. Please create a registration first.")
        return False
    
    print(f"✓ Found {registrations.count()} registrations")
    
    for reg in registrations:
        print(f"\n📋 Registration: {reg.registration_number}")
        print(f"   Attendee: {reg.attendee_name}")
        print(f"   Email: {reg.attendee_email}")
        print(f"   QR Code: {reg.qr_code}")
        
        # Test QR code generation
        try:
            qr_image = reg.generate_qr_code_image()
            if qr_image and len(qr_image) > 100:
                print(f"   ✓ QR code generated successfully ({len(qr_image)} bytes)")
            else:
                print(f"   ❌ QR code generation failed")
                return False
        except Exception as e:
            print(f"   ❌ Error generating QR code: {e}")
            return False
    
    print("\n✅ All QR codes generated successfully!")
    return True


def test_email_function():
    """Test email sending function (without actually sending)"""
    print("\n" + "=" * 60)
    print("Testing Email Function")
    print("=" * 60)
    
    registration = Registration.objects.first()
    
    if not registration:
        print("❌ No registrations found")
        return False
    
    print(f"✓ Testing with registration: {registration.registration_number}")
    
    try:
        from registration.views_success import send_qr_email_direct
        
        # Note: This will actually send an email if SMTP is configured
        # Comment out the next line if you don't want to send test emails
        # send_qr_email_direct(registration)
        
        print("✓ Email function is available")
        print("⚠️  Actual email sending skipped (uncomment to test)")
        return True
    except Exception as e:
        print(f"❌ Error with email function: {e}")
        return False


def test_success_page_data():
    """Test success page data preparation"""
    print("\n" + "=" * 60)
    print("Testing Success Page Data")
    print("=" * 60)
    
    registration = Registration.objects.first()
    
    if not registration:
        print("❌ No registrations found")
        return False
    
    print(f"✓ Testing with registration: {registration.registration_number}")
    
    # Simulate success page data
    try:
        qr_code_image = registration.generate_qr_code_image()
        event = registration.event
        
        context = {
            'registration': registration,
            'event': event,
            'qr_code_image': qr_code_image,
        }
        
        print(f"✓ Event: {event.title}")
        print(f"✓ Registration Number: {registration.registration_number}")
        print(f"✓ QR Code Size: {len(qr_code_image)} bytes")
        print(f"✓ Success URL: /registration/success/{registration.id}/")
        
        return True
    except Exception as e:
        print(f"❌ Error preparing success page data: {e}")
        return False


def test_api_response():
    """Test API response format"""
    print("\n" + "=" * 60)
    print("Testing API Response Format")
    print("=" * 60)
    
    registration = Registration.objects.first()
    
    if not registration:
        print("❌ No registrations found")
        return False
    
    # Simulate API response
    response_data = {
        'id': registration.id,
        'registration_number': registration.registration_number,
        'message': 'Registration successful!',
        'status': registration.status,
        'total_amount': str(registration.total_amount),
        'success_url': f'/registration/success/{registration.id}/'
    }
    
    print("✓ API Response Format:")
    for key, value in response_data.items():
        print(f"   {key}: {value}")
    
    return True


def main():
    """Run all tests"""
    print("\n🚀 Starting QR Code Registration Feature Tests\n")
    
    tests = [
        test_qr_code_generation,
        test_email_function,
        test_success_page_data,
        test_api_response,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Please review the output above.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
