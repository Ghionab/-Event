# Gate Staff Portal - Quick Command Reference

## Running the Portals

### All Three Portals

```bash
# Terminal 1 - Organizer Portal (Port 8000)
python manage.py runserver 8000

# Terminal 2 - Participant Portal (Port 8001)
python manage.py runserver 8001 --settings=event_project.settings_participant

# Terminal 3 - Gate Staff Portal (Port 8002) ✨ NEW
python run_staff_portal.py
# OR
python manage.py runserver 8002 --settings=event_project.settings_staff
```

## Creating Staff Users

### Via Django Shell
```bash
python manage.py shell
```

```python
from users.models import User

# Create staff user
User.objects.create_user(
    email='staff@example.com',
    password='staffpass123',
    first_name='John',
    last_name='Doe',
    role='staff'
)

# Create multiple staff users
for i in range(1, 4):
    User.objects.create_user(
        email=f'gate{i}@event.com',
        password='gatepass123',
        first_name=f'Gate',
        last_name=f'Staff {i}',
        role='staff'
    )
```

### Via Django Admin
1. Navigate to `http://localhost:8000/admin/`
2. Go to Users
3. Add user
4. Set role to "Gate Staff"

## Testing the Portal

### Create Test Event with Registrations
```bash
python manage.py shell
```

```python
from events.models import Event
from registration.models import Registration, TicketType
from users.models import User
from django.utils import timezone
from datetime import timedelta

# Get or create organizer
organizer = User.objects.filter(role='organizer').first()
if not organizer:
    organizer = User.objects.create_user(
        email='organizer@test.com',
        password='test123',
        role='organizer'
    )

# Create test event (today)
event = Event.objects.create(
    title="Test Conference 2026",
    description="Test event for staff portal",
    start_date=timezone.now().date(),
    end_date=timezone.now().date() + timedelta(days=1),
    venue_name="Convention Center",
    organizer=organizer,
    status='published'
)

# Create ticket type
ticket = TicketType.objects.create(
    event=event,
    name="General Admission",
    description="Standard entry ticket",
    price=0,
    quantity_available=100,
    sales_start=timezone.now() - timedelta(days=7),
    sales_end=timezone.now() + timedelta(days=1)
)

# Create 20 test registrations
for i in range(1, 21):
    Registration.objects.create(
        event=event,
        ticket_type=ticket,
        attendee_name=f"Test Attendee {i}",
        attendee_email=f"attendee{i}@test.com",
        attendee_phone=f"+1234567{i:04d}",
        status='confirmed',
        total_amount=0
    )

print(f"Created event: {event.title}")
print(f"Created {Registration.objects.filter(event=event).count()} registrations")
```

## Accessing the Portals

### URLs
- **Organizer Portal**: http://localhost:8000
- **Participant Portal**: http://localhost:8001
- **Staff Portal**: http://localhost:8002

### Default Login Credentials (After Creating)
- **Staff**: staff@example.com / staffpass123
- **Organizer**: organizer@test.com / test123

## Database Operations

### Check Staff Users
```bash
python manage.py shell
```

```python
from users.models import User

# List all staff users
staff_users = User.objects.filter(role='staff')
for user in staff_users:
    print(f"{user.email} - {user.get_full_name()}")

# Count by role
from django.db.models import Count
User.objects.values('role').annotate(count=Count('id'))
```

### Check Registrations
```python
from registration.models import Registration

# Total registrations
print(f"Total: {Registration.objects.count()}")

# By status
from django.db.models import Count
Registration.objects.values('status').annotate(count=Count('id'))

# Checked in today
from django.utils import timezone
today = timezone.now().date()
checked_in_today = Registration.objects.filter(
    checked_in_at__date=today
).count()
print(f"Checked in today: {checked_in_today}")
```

## Migrations

### Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Check Migration Status
```bash
python manage.py showmigrations
```

## Troubleshooting Commands

### Clear Sessions
```bash
python manage.py clearsessions
```

### Check for Issues
```bash
python manage.py check
```

### Create Superuser
```bash
python manage.py createsuperuser
```

## Development Tips

### Run with Different Settings
```bash
# Organizer portal
python manage.py runserver 8000

# Participant portal
python manage.py runserver 8001 --settings=event_project.settings_participant

# Staff portal
python manage.py runserver 8002 --settings=event_project.settings_staff
```

### View Logs
The staff portal logs to console. Watch for:
- Authentication attempts
- Check-in operations
- API calls
- Errors

### Test API Endpoints
```bash
# Using curl (after logging in and getting session cookie)
curl -X POST http://localhost:8002/api/v1/events/1/registrations/1/check-in/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  --cookie "staff_sessionid=YOUR_SESSION_ID"
```

## Quick Reset

### Reset All Check-ins
```bash
python manage.py shell
```

```python
from registration.models import Registration, CheckIn

# Reset all registrations to confirmed
Registration.objects.filter(status='checked_in').update(
    status='confirmed',
    checked_in_at=None,
    checked_in_by=None
)

# Delete all check-in logs
CheckIn.objects.all().delete()

print("All check-ins reset!")
```

## Production Deployment

### Environment Variables
```bash
# Set production settings
export DJANGO_SETTINGS_MODULE=event_project.settings_staff
export DEBUG=False
export SECRET_KEY='your-production-secret-key'
export ALLOWED_HOSTS='your-domain.com'
```

### Collect Static Files
```bash
python manage.py collectstatic --settings=event_project.settings_staff
```

### Run with Gunicorn
```bash
gunicorn event_project.wsgi:application \
  --bind 0.0.0.0:8002 \
  --workers 3 \
  --env DJANGO_SETTINGS_MODULE=event_project.settings_staff
```

## Useful Queries

### Check-in Statistics
```python
from registration.models import Registration
from django.db.models import Count, Q

# Get stats for an event
event_id = 1
stats = Registration.objects.filter(event_id=event_id).aggregate(
    total=Count('id'),
    confirmed=Count('id', filter=Q(status='confirmed')),
    checked_in=Count('id', filter=Q(status='checked_in'))
)
print(stats)
```

### Recent Check-ins
```python
from registration.models import CheckIn

# Last 10 check-ins
recent = CheckIn.objects.select_related(
    'registration', 'checked_in_by'
).order_by('-check_in_time')[:10]

for checkin in recent:
    print(f"{checkin.registration.attendee_name} - {checkin.check_in_time}")
```

## Support

For issues:
1. Check Django logs in console
2. Check browser console (F12)
3. Verify database migrations
4. Test API endpoints directly
5. Review STAFF_PORTAL_GUIDE.md
