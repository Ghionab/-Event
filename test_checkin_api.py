"""
Test script for check-in API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_staff')
django.setup()

from registration.models import Registration, RegistrationStatus
from events.models import Event

print("=" * 60)
print("CHECK-IN API TEST")
print("=" * 60)

# Get first event
event = Event.objects.first()
if not event:
    print("❌ No events found in database")
    exit(1)

print(f"\n✓ Testing with Event: {event.title} (ID: {event.id})")

# Get registrations
confirmed_regs = Registration.objects.filter(
    event=event,
    status=RegistrationStatus.CONFIRMED
)

checked_in_regs = Registration.objects.filter(
    event=event,
    status=RegistrationStatus.CHECKED_IN
)

print(f"\n📊 Registration Stats:")
print(f"   - Confirmed: {confirmed_regs.count()}")
print(f"   - Checked In: {checked_in_regs.count()}")

# Show sample registration with QR code
if confirmed_regs.exists():
    sample = confirmed_regs.first()
    print(f"\n📝 Sample Registration:")
    print(f"   - ID: {sample.id}")
    print(f"   - Name: {sample.attendee_name}")
    print(f"   - Email: {sample.attendee_email}")
    print(f"   - Status: {sample.status}")
    print(f"   - QR Code: {sample.qr_code}")
    print(f"   - Registration #: {sample.registration_number}")
    
    print(f"\n🔗 API Endpoints:")
    print(f"   - List: GET /api/v1/events/{event.id}/registrations/")
    print(f"   - Check-in: POST /api/v1/events/{event.id}/registrations/{sample.id}/check-in/")
    
    print(f"\n✅ API is ready to use!")
    print(f"\n💡 To test:")
    print(f"   1. Start server: python manage.py runserver 8002 --settings=event_project.settings_staff")
    print(f"   2. Login at: http://localhost:8002/staff/login/")
    print(f"   3. Go to event dashboard: http://localhost:8002/staff/events/{event.id}/")
    print(f"   4. Click 'Start Scanning' and scan QR code: {sample.qr_code}")
else:
    print("\n⚠️  No confirmed registrations found")
    print("   Create some registrations first!")

print("\n" + "=" * 60)
