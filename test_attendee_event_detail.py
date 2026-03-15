#!/usr/bin/env python
"""
Test script to verify the attendee event detail page works correctly
"""
import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_participant')
django.setup()

def test_event_detail_page():
    """Test that the event detail page loads correctly with sessions"""
    client = Client()
    
    # Test with event ID 7 (ai course)
    event_id = 7
    
    try:
        # Get the URL for the event detail page
        url = reverse('participant_event_detail', args=[event_id])
        print(f"Testing URL: {url}")
        
        # Make a GET request
        response = client.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page loaded successfully")
            
            # Check if the response contains our "Sessions & Speakers" section
            content = response.content.decode('utf-8')
            
            # Check for key elements
            if 'Sessions & Speakers' in content:
                print("✅ 'Sessions & Speakers' section found")
            else:
                print("❌ 'Sessions & Speakers' section NOT found")
                
            # Check for session title
            if 'Initial Session' in content:
                print("✅ Session title 'Initial Session' found")
            else:
                print("❌ Session title 'Initial Session' NOT found")
                
            # Check for speaker name
            if 'Speaker 1' in content:
                print("✅ Speaker name 'Speaker 1' found")
            else:
                print("❌ Speaker name 'Speaker 1' NOT found")
                
            # Check for speaker profile picture URL pattern
            if 'speaker_profile_picture' in content:
                print("✅ Speaker profile picture reference found")
            else:
                print("❌ Speaker profile picture reference NOT found")
                
        else:
            print(f"❌ Page failed to load. Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing event detail page: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("Testing Attendee Event Detail Page")
    print("=" * 60)
    test_event_detail_page()
    print("=" * 60)