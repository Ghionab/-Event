"""
Generate QR codes for testing check-in
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_staff')
django.setup()

from registration.models import Registration, RegistrationStatus
from events.models import Event
import qrcode

# Get first event
event = Event.objects.first()
if not event:
    print("No events found")
    exit(1)

# Get confirmed registrations
registrations = Registration.objects.filter(
    event=event,
    status=RegistrationStatus.CONFIRMED
)[:5]

print(f"Generating QR codes for {event.title}")
print("=" * 60)

for reg in registrations:
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(reg.qr_code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"qr_{reg.registration_number}.png"
    img.save(filename)
    
    print(f"✓ {reg.attendee_name} - {filename}")
    print(f"  QR Code: {reg.qr_code}")
    print(f"  Registration: {reg.registration_number}")
    print()

print(f"\n✅ Generated {registrations.count()} QR codes")
print("You can now scan these with your phone to test check-in!")
