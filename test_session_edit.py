import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from events.models import Event, Session
from organizers.views import event_edit

User = get_user_model()

def test_session_edit():
    print("Setting up test data...")
    user = User.objects.filter(role='organizer').first()
    if not user:
        # Create user if missing
        user = User.objects.create(email='test_org@example.com', role='organizer', is_active=True)
        user.set_password('password')
        user.save()

    event = Event.objects.filter(organizer=user).first()
    if not event:
        event = Event.objects.create(
            title="Test Event For Editing",
            organizer=user,
            description="Testing session edits",
            status="draft"
        )
    
    # Create an initial session
    Session.objects.filter(event=event).delete()
    session1 = Session.objects.create(
        event=event,
        title="Initial Session",
        speaker_name="Speaker 1",
        speaker_bio="Bio 1"
    )

    print(f"Created event '{event.title}' with session '{session1.title}' (ID: {session1.id})")

    # Simulate POST request to edit and add a session
    post_data = {
        # Formset management data
        'dynamic_sessions-TOTAL_FORMS': '2',
        'dynamic_sessions-INITIAL_FORMS': '1',
        'dynamic_sessions-MIN_NUM_FORMS': '0',
        'dynamic_sessions-MAX_NUM_FORMS': '1000',
        # Existing session data update
        'dynamic_sessions-0-id': str(session1.id),
        'dynamic_sessions-0-title': "Updated Session Title",
        'dynamic_sessions-0-speaker_name': "Updated Speaker 1",
        'dynamic_sessions-0-speaker_bio': "Updated Bio 1",
        # New session data
        'dynamic_sessions-1-id': '',
        'dynamic_sessions-1-title': "Brand New Session",
        'dynamic_sessions-1-speaker_name': "Speaker 2",
        'dynamic_sessions-1-speaker_bio': "Bio 2",
    }
    
    from events.forms import SessionFormSet
    
    print("Testing SessionFormSet directly...")
    formset = SessionFormSet(post_data, instance=event)
    
    if formset.is_valid():
        print("Formset is valid! Saving...")
        formset.save()
        
        # Verify db logic
        sessions = Session.objects.filter(event=event).order_by('id')
        print(f"\nFinal session count for event: {sessions.count()}")
        for s in sessions:
            print(f"- Session ID {s.id}: Title='{s.title}', Speaker='{s.speaker_name}'")

        assert sessions.count() == 2, "Should have 2 sessions"
        assert sessions[0].title == "Updated Session Title", "First session should be updated"
        assert sessions[1].title == "Brand New Session", "Second session should be newly added"
        print("\nAll database checks passed! Edit logic works flawlessly.")
    else:
        print("Formset validation failed!")
        print(formset.errors)
        sys.exit(1)

if __name__ == '__main__':
    test_session_edit()
