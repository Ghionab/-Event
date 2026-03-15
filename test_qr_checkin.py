#!/usr/bin/env python
"""
Test QR check-in functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_staff')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from registration.models import Registration

User = get_user_model()

def test_qr_checkin():
    # Create a test client
    client = Client()
    
    # Get a staff user
    try:
        staff_user = User.objects.filter(role__in=['admin', 'organizer', 'staff']).first()
        if not staff_user:
            print("No staff user found. Creating one...")
            staff_user = User.objects.create_user(
                email='staff@test.com',
                password='testpass123',
                first_name='Test',
                last_name='Staff',
                role='staff'
            )
        print(f"Using staff user: {staff_user.email}")
    except Exception as e:
        print(f"Error getting staff user: {e}")
        return
    
    # Login as staff
    client.force_login(staff_user)
    
    # Get a confirmed registration
    registration = Registration.objects.filter(status='confirmed').first()
    if not registration:
        print("No confirmed registrations found")
        return
    
    print(f"Testing QR check-in for:")
    print(f"  Event ID: {registration.event.id}")
    print(f"  Registration ID: {registration.id}")
    print(f"  Attendee: {registration.attendee_name}")
    print(f"  QR Code: {registration.qr_code}")
    print(f"  Status: {registration.status}")
    
    # Test the QR check-in endpoint
    url = f'/staff/events/{registration.event.id}/qr-checkin/'
    data = {'qr_code': registration.qr_code}
    
    print(f"\nTesting POST to: {url}")
    print(f"Data: {data}")
    
    response = client.post(url, data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.json()}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✓ QR check-in successful!")
        else:
            print(f"✗ QR check-in failed: {result.get('message')}")
    else:
        print(f"✗ HTTP error: {response.status_code}")

if __name__ == '__main__':
    test_qr_checkin()
