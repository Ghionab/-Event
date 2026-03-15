"""
Test script to verify usher functionality
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from users.models import User
from events.models import Event
from advanced.models import UsherAssignment

print("=== Testing Usher System ===\n")

# 1. Check if usher role exists
print("1. Checking user roles...")
users = User.objects.all()[:5]
for u in users:
    print(f"   - {u.email}: role={u.role}")

# 2. Check existing usher assignments
print("\n2. Checking usher assignments...")
assignments = UsherAssignment.objects.all()
print(f"   Total assignments: {assignments.count()}")
for a in assignments:
    print(f"   - {a.user.email} | Event: {a.event.title} | Venue: {a.venue_name} | Active: {a.is_active}")

# 3. Test URL reversing
print("\n3. Testing URL reversing...")
from django.urls import reverse
try:
    url = reverse('organizers:organizer_dashboard')
    print(f"   organizers:organizer_dashboard -> {url}")
except Exception as e:
    print(f"   ERROR: {e}")

try:
    url = reverse('organizer_dashboard')
    print(f"   organizer_dashboard -> {url}")
except Exception as e:
    print(f"   ERROR: {e}")

# 4. Check staff decorator
print("\n4. Testing staff decorator...")
from staff.decorators import staff_required
print(f"   Staff allowed roles: admin, organizer, staff, usher")

# 5. Create test usher if none exists
print("\n5. Creating test usher...")
test_email = 'usher_test@example.com'
usher_user, created = User.objects.get_or_create(
    email=test_email,
    defaults={
        'role': 'usher',
        'first_name': 'Test',
        'last_name': 'Usher'
    }
)
if created:
    usher_user.set_password('testpass123')
    usher_user.save()
    print(f"   Created new user: {test_email}")
else:
    print(f"   User already exists: {test_email}")

# Assign to an event
event = Event.objects.first()
if event:
    assignment, created = UsherAssignment.objects.get_or_create(
        user=usher_user,
        event=event,
        venue_name=event.venue_name or 'Main Hall',
        defaults={'is_active': True}
    )
    if created:
        print(f"   Created assignment: {usher_user.email} -> {event.title}")
    else:
        print(f"   Assignment already exists")

print("\n=== Test Complete ===")
