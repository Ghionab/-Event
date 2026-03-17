#!/usr/bin/env python
"""
Debug test to check what's happening with the event detail page
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_participant')
django.setup()

from django.test import Client
from django.urls import reverse

def debug_event_detail():
    """Debug the event detail page"""
    client = Client()
    
    # Test with event ID 7
    event_id = 7
    
    try:
        # Get the URL for the event detail page
        url = reverse('participant_event_detail', args=[event_id])
        print(f"URL: {url}")
        
        # Make a GET request
        response = client.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Page loaded successfully")
            
            # Check template
            if hasattr(response, 'template_name'):
                print(f"Template used: {response.template_name}")
            else:
                print("No template_name attribute")
                
            # Check context
            if hasattr(response, 'context'):
                print(f"Context keys: {list(response.context.keys())}")
                
                # Check for dynamic_sessions
                if 'dynamic_sessions' in response.context:
                    sessions = response.context['dynamic_sessions']
                    print(f"dynamic_sessions found: {sessions}")
                    if sessions:
                        print(f"Number of dynamic sessions: {sessions.count()}")
                        for s in sessions:
                            print(f"  - {s.title}: {s.speaker_name}")
                    else:
                        print("dynamic_sessions is empty")
                else:
                    print("dynamic_sessions NOT in context")
                    
                # Check for sessions (EventSession)
                if 'sessions' in response.context:
                    event_sessions = response.context['sessions']
                    print(f"sessions found: {event_sessions}")
                else:
                    print("sessions NOT in context")
            else:
                print("No context attribute")
                
            # Check response content for key strings
            content = response.content.decode('utf-8')
            
            # Look for our section
            if 'Sessions & Speakers' in content:
                print("✓ 'Sessions & Speakers' found in content")
            else:
                print("✗ 'Sessions & Speakers' NOT found in content")
                
            # Check for template markers
            if '{% if dynamic_sessions %}' in content:
                print("✓ Template conditional found")
            else:
                print("✗ Template conditional NOT found")
                
        else:
            print(f"Page failed to load. Status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("Debugging Attendee Event Detail Page")
    print("=" * 60)
    debug_event_detail()
    print("=" * 60)