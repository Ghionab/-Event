import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event, Session

User = get_user_model()

def run_test():
    # 1. Get or create an organizer user
    user, created = User.objects.get_or_create(
        username='test_organizer',
        defaults={'email': 'test@example.com', 'password': 'password123'}
    )
    
    # 2. Create an event
    from django.utils import timezone
    from datetime import timedelta
    event = Event.objects.create(
        title='Test Dynamic Sessions Event',
        description='Testing the dynamic sessions feature.',
        start_date=timezone.now() + timedelta(days=1),
        end_date=timezone.now() + timedelta(days=2),
        organizer=user
    )
    print(f"Created event: {event.title} (ID: {event.id})")
    
    # 3. Create some dynamic sessions
    session1 = Session.objects.create(
        event=event,
        title='Keynote: The Future of Events',
        speaker_name='Jane Doe',
        speaker_bio='An expert in event management.'
    )
    
    session2 = Session.objects.create(
        event=event,
        title='Workshop: Django for Beginners',
        speaker_name='John Smith',
        speaker_bio='A seasoned Django developer.'
    )
    print(f"Created {event.dynamic_sessions.count()} sessions for the event.")
    
    # 4. Verify they can be retrieved
    sessions = event.dynamic_sessions.all()
    print("Retrieved sessions:")
    for s in sessions:
        print(f" - {s.title} by {s.speaker_name}")
        
    print("Test passed successfully!")

if __name__ == '__main__':
    run_test()
