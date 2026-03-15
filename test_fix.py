import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_staff')
django.setup()

from registration.models import Registration, RegistrationStatus
from events.models import Event

print("Testing check-in fix...")
print("=" * 60)

# Get a confirmed registration
reg = Registration.objects.filter(status=RegistrationStatus.CONFIRMED).first()
if reg:
    print(f"✓ Found test registration:")
    print(f"  ID: {reg.id}")
    print(f"  Name: {reg.attendee_name}")
    print(f"  Event: {reg.event.title} (ID: {reg.event.id})")
    print(f"  QR Code: {reg.qr_code}")
    print(f"\n✓ API Endpoint:")
    print(f"  POST /api/v1/events/{reg.event.id}/registrations/{reg.id}/check-in/")
    print(f"\n✓ Manual Check-in:")
    print(f"  POST /staff/checkin/{reg.id}/")
    print(f"\n✓ Test at: http://localhost:8002/staff/events/{reg.event.id}/")
else:
    print("❌ No confirmed registrations found")

print("=" * 60)
print("\nChanges made:")
print("1. ✓ Changed RegistrationViewSet permission to IsAuthenticated")
print("2. ✓ Added 'staff' role to get_queryset()")
print("3. ✓ Fixed CSRF_USE_SESSIONS = False")
print("4. ✓ Added REST_FRAMEWORK settings")
print("5. ✓ Enhanced getCSRFToken() function")
print("\nNow restart server and test!")
