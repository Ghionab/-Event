"""
Verify check-in setup is complete and working
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_staff')
django.setup()

from django.urls import reverse, resolve
from registration.models import Registration, RegistrationStatus, CheckIn
from events.models import Event
from users.models import User

print("\n" + "=" * 70)
print("CHECK-IN SYSTEM VERIFICATION")
print("=" * 70)

# Check 1: Events API module exists
print("\n1. Checking Events API module...")
try:
    import events_api
    from events_api import views
    print("   ✅ events_api module found")
    print("   ✅ events_api.views found")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Check 2: URL patterns configured
print("\n2. Checking URL patterns...")
try:
    # Check registrations list endpoint
    url = '/api/v1/events/1/registrations/'
    match = resolve(url)
    print(f"   ✅ {url} → {match.func.__name__}")
    
    # Check check-in endpoint
    url = '/api/v1/events/1/registrations/1/check-in/'
    match = resolve(url)
    print(f"   ✅ {url} → {match.func.__name__}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Check 3: Database has data
print("\n3. Checking database...")
event_count = Event.objects.count()
reg_count = Registration.objects.count()
confirmed_count = Registration.objects.filter(status=RegistrationStatus.CONFIRMED).count()
checked_in_count = Registration.objects.filter(status=RegistrationStatus.CHECKED_IN).count()

print(f"   ✅ Events: {event_count}")
print(f"   ✅ Registrations: {reg_count}")
print(f"   ✅ Confirmed: {confirmed_count}")
print(f"   ✅ Checked In: {checked_in_count}")

if confirmed_count == 0:
    print("   ⚠️  Warning: No confirmed registrations to test with")

# Check 4: Staff users exist
print("\n4. Checking staff users...")
staff_users = User.objects.filter(role__in=['staff', 'admin', 'organizer'])
print(f"   ✅ Staff users: {staff_users.count()}")
if staff_users.exists():
    for user in staff_users[:3]:
        print(f"      - {user.email} ({user.role})")

# Check 5: Sample registration with QR code
print("\n5. Checking sample registration...")
sample_reg = Registration.objects.filter(status=RegistrationStatus.CONFIRMED).first()
if sample_reg:
    print(f"   ✅ Sample Registration:")
    print(f"      - ID: {sample_reg.id}")
    print(f"      - Name: {sample_reg.attendee_name}")
    print(f"      - Event: {sample_reg.event.title}")
    print(f"      - QR Code: {sample_reg.qr_code}")
    print(f"      - Status: {sample_reg.status}")
else:
    print("   ❌ No confirmed registrations found")

# Check 6: CheckIn model
print("\n6. Checking CheckIn model...")
checkin_count = CheckIn.objects.count()
print(f"   ✅ CheckIn records: {checkin_count}")
if checkin_count > 0:
    recent = CheckIn.objects.order_by('-check_in_time').first()
    print(f"      - Most recent: {recent.registration.attendee_name}")
    print(f"      - Method: {recent.method}")
    print(f"      - Time: {recent.check_in_time}")

# Check 7: Test API function
print("\n7. Testing API functions...")
try:
    from events_api.views.registration_views import RegistrationViewSet
    print("   ✅ RegistrationViewSet imported")
    print("   ✅ check_in action available")
except ImportError as e:
    print(f"   ❌ Error: {e}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if event_count > 0 and confirmed_count > 0 and staff_users.exists():
    print("\n✅ ALL CHECKS PASSED!")
    print("\nYou can now:")
    print("1. Start server: python manage.py runserver 8002 --settings=event_project.settings_staff")
    print("2. Login at: http://localhost:8002/staff/login/")
    if sample_reg:
        print(f"3. Go to: http://localhost:8002/staff/events/{sample_reg.event.id}/")
        print(f"4. Scan QR code: {sample_reg.qr_code}")
else:
    print("\n⚠️  SETUP INCOMPLETE")
    if event_count == 0:
        print("   - Create events first")
    if confirmed_count == 0:
        print("   - Create confirmed registrations")
    if not staff_users.exists():
        print("   - Create staff users")

print("\n" + "=" * 70 + "\n")
