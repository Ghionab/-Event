#!/usr/bin/env python
"""
Setup script to create a test coordinator assignment
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event
from advanced.models import TeamMember, TeamRole

User = get_user_model()

def create_test_coordinator():
    """Create a test coordinator user and assignment"""
    
    # Create or get test coordinator user
    coordinator_email = "coordinator@test.com"
    user, created = User.objects.get_or_create(
        email=coordinator_email,
        defaults={
            'first_name': 'Test',
            'last_name': 'Coordinator',
            'is_active': True,
        }
    )
    
    if created:
        user.set_password('coordinator123')
        user.save()
        print(f"✅ Created coordinator user: {coordinator_email}")
    else:
        print(f"📋 Coordinator user already exists: {coordinator_email}")
    
    # Get first event for assignment
    event = Event.objects.first()
    if not event:
        print("❌ No events found. Please create an event first.")
        return
    
    # Create coordinator assignment
    team_member, created = TeamMember.objects.get_or_create(
        user=user,
        event=event,
        defaults={
            'role': TeamRole.COORDINATOR,
            'department': 'Event Coordination',
            'can_manage_registrations': False,  # Coordinators can't manage registrations
            'can_manage_sessions': True,
            'can_manage_sponsors': True,
            'can_view_financials': False,  # Coordinators can't view financials
            'can_manage_team': False,  # Coordinators can't manage team
            'is_active': True,
        }
    )
    
    if created:
        print(f"✅ Assigned coordinator to event: {event.title}")
    else:
        print(f"📋 Coordinator assignment already exists for event: {event.title}")
    
    print(f"\n🎯 Test Coordinator Setup Complete!")
    print(f"📧 Email: {coordinator_email}")
    print(f"🔑 Password: coordinator123")
    print(f"🎪 Assigned Event: {event.title}")
    print(f"🌐 Coordinator Portal: http://localhost:8003/coordinators/")
    
    return user, event

if __name__ == "__main__":
    create_test_coordinator()
