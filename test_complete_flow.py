#!/usr/bin/env python
"""Test complete registration flow with QR code"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_participant')
django.setup()

import requests
import json

def test_complete_registration_flow():
    """Test the complete registration flow"""
    
    print("Testing Complete Registration Flow with QR Code")
    print("=" * 60)
    
    # Test data
    registration_data = {
        "event_id": 8,
        "full_name": "Test User QR",
        "email": "testqr@example.com",
        "phone": "+1234567890",
        "special_requests": "Test QR code functionality",
        "tickets": [
            {
                "ticket_id": 7,  # Standard Ticket
                "quantity": 1
            }
        ]
    }
    
    print("1. Testing Registration API...")
    print(f"   URL: http://localhost:8001/api/v1/register/")
    print(f"   Data: {json.dumps(registration_data, indent=2)}")
    
    try:
        response = requests.post(
            'http://localhost:8001/api/v1/register/',
            json=registration_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   Registration successful!")
            print(f"   Registration ID: {data.get('id')}")
            print(f"   Registration Number: {data.get('registration_number')}")
            print(f"   Status: {data.get('status')}")
            
            registration_id = data.get('id')
            
            if registration_id:
                print(f"\n2. Testing Registration Success Page...")
                success_url = f"http://localhost:8001/registration/success/{registration_id}/"
                print(f"   URL: {success_url}")
                
                success_response = requests.get(success_url)
                print(f"   Status: {success_response.status_code}")
                
                if success_response.status_code == 200:
                    print("   Success page accessible!")
                    
                    # Check if QR code is mentioned in page
                    if 'qr' in success_response.text.lower():
                        print("   QR code section found in page!")
                    else:
                        print("   QR code section not found in page")
                else:
                    print(f"   Success page not accessible: {success_response.status_code}")
                
                print(f"\n3. Testing QR Code Email API...")
                email_data = {"registration_id": registration_id}
                
                email_response = requests.post(
                    'http://localhost:8001/api/v1/send-qr-email/',
                    json=email_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                print(f"   Status: {email_response.status_code}")
                email_result = email_response.json()
                
                if email_response.status_code == 200 and email_result.get('success'):
                    print("   QR code email API working!")
                    print(f"   Message: {email_result.get('message')}")
                else:
                    print("   QR code email API failed!")
                    print(f"   Error: {email_result.get('error', 'Unknown error')}")
            else:
                print("   No registration ID in response")
        else:
            print(f"   Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("REGISTRATION FLOW TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_registration_flow()
