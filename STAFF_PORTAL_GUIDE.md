# Gate Staff Portal - Complete Guide

## Overview

The Gate Staff Portal is a lightweight, mobile-responsive Django application designed for event check-in staff ("bouncers") to manage attendee entry at event venues. It runs on **Port 8002** as the third portal in the Event Management System.

## Architecture

### Three-Portal System
1. **Organizer Portal** (Port 8000) - Event management and administration
2. **Participant Portal** (Port 8001) - Public event registration and attendee features
3. **Gate Staff Portal** (Port 8002) - Check-in and entry management ✨ NEW

### Key Files
- `event_project/settings_staff.py` - Staff portal configuration
- `event_project/urls_staff.py` - Staff portal URL routing
- `staff/` - Staff portal Django app
- `run_staff_portal.py` - Quick start script

## Features

### 1. Authentication & Access Control
- Restricted to users with **ADMIN**, **ORGANIZER**, or **STAFF** roles
- Secure login with session management (8-hour sessions)
- Staff badge display showing logged-in user

### 2. Event Dashboard
- List of active events (today or future)
- Real-time statistics:
  - Total Registered
  - Total Checked In
  - Check-in Rate (%)
- Event selection for check-in management

### 3. QR Code Scanner
- Mobile-responsive camera access using `html5-qrcode` library
- Real-time QR code scanning
- Automatic check-in via API endpoint
- Visual feedback:
  - ✅ **Green** - Check-in successful
  - ⚠️ **Yellow** - Already checked in
  - ❌ **Red** - Invalid ticket or error

### 4. Attendee List & Manual Check-in
- Searchable list of all registered attendees
- Search by:
  - Name
  - Email
  - Registration number
- Manual check-in button for each attendee
- Visual status indicators:
  - Yellow badge: Confirmed (not checked in)
  - Green badge: Checked In

### 5. Live Statistics
- Real-time counter updates
- Auto-refresh every 30 seconds
- Check-in rate percentage
- Recent check-ins log

## Installation & Setup

### 1. Add STAFF Role to User Model
The STAFF role has been added to `users/models.py`:

```python
class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    ORGANIZER = 'organizer', 'Event Organizer'
    STAFF = 'staff', 'Gate Staff'  # NEW
    SPEAKER = 'speaker', 'Speaker'
    SPONSOR = 'sponsor', 'Sponsor'
    ATTENDEE = 'attendee', 'Attendee'
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Staff Users
You can create staff users via Django admin or shell:

```python
python manage.py shell

from users.models import User

# Create a staff user
staff = User.objects.create_user(
    email='staff@example.com',
    password='staffpassword123',
    first_name='John',
    last_name='Staff',
    role='staff'
)
```

## Running the Portal

### Method 1: Using the Quick Start Script
```bash
python run_staff_portal.py
```

### Method 2: Using manage.py
```bash
python manage.py runserver 8002 --settings=event_project.settings_staff
```

### Method 3: Environment Variable
```bash
# Windows
set DJANGO_SETTINGS_MODULE=event_project.settings_staff
python manage.py runserver 8002

# Linux/Mac
export DJANGO_SETTINGS_MODULE=event_project.settings_staff
python manage.py runserver 8002
```

## Usage Guide

### For Gate Staff

1. **Login**
   - Navigate to `http://localhost:8002`
   - Login with staff credentials
   - You'll see your staff badge at the top

2. **Select Event**
   - View list of active events
   - See registration and check-in statistics
   - Click "Open" to access event dashboard

3. **QR Code Scanning**
   - Click "Start Scanning" button
   - Allow camera access when prompted
   - Point camera at attendee's QR code
   - System automatically checks in and shows confirmation
   - Scanner pauses briefly after each scan

4. **Manual Check-in**
   - Use search box to find attendee
   - Click "Check In" button next to their name
   - Confirm the action
   - Status updates immediately

5. **Monitor Statistics**
   - View real-time check-in progress
   - Statistics auto-refresh every 30 seconds
   - Check-in rate percentage displayed

### For Administrators

1. **Create Staff Users**
   ```python
   from users.models import User
   
   User.objects.create_user(
       email='gate1@event.com',
       password='secure_password',
       first_name='Gate',
       last_name='Staff 1',
       role='staff'
   )
   ```

2. **Assign Staff to Events**
   - Currently, all staff can access all active events
   - Future enhancement: Event-specific staff assignments

3. **Monitor Check-ins**
   - Access organizer portal for detailed analytics
   - View check-in logs and history
   - Export check-in reports

## API Endpoints Used

The staff portal uses the existing API endpoints:

### Check-in Endpoint
```
POST /api/v1/events/{event_id}/registrations/{registration_id}/check-in/
```

**Response (Success):**
```json
{
    "message": "Checked in successfully",
    "checked_in_at": "2026-03-11T15:30:00Z"
}
```

**Response (Already Checked In):**
```json
{
    "error": "Already checked in"
}
```

### Registration List
```
GET /api/v1/events/{event_id}/registrations/
```

### Stats Endpoint (Staff Portal)
```
GET /staff/events/{event_id}/stats/
```

**Response:**
```json
{
    "total_registered": 150,
    "total_checked_in": 87,
    "check_in_rate": 58.0,
    "recent_checkins": [...]
}
```

## Mobile Optimization

The portal is fully optimized for mobile devices:

- Responsive design using Bootstrap 5
- Touch-friendly buttons (minimum 44px)
- Camera access for QR scanning
- Optimized viewport settings
- No horizontal scrolling
- Large, readable text
- Easy-to-tap check-in buttons

### Recommended Devices
- Smartphones (iOS/Android)
- Tablets
- Desktop browsers

### Browser Compatibility
- Chrome (recommended)
- Safari
- Firefox
- Edge

## Security Features

1. **Role-Based Access Control**
   - Only ADMIN, ORGANIZER, and STAFF roles allowed
   - Decorator-based permission checking

2. **CSRF Protection**
   - All POST requests require CSRF token
   - Session-based authentication

3. **Session Management**
   - 8-hour session timeout
   - Separate session cookie (`staff_sessionid`)
   - HTTP-only cookies

4. **API Security**
   - Authentication required for all check-in operations
   - User tracking for audit logs

## Troubleshooting

### Camera Not Working
- **Issue**: QR scanner can't access camera
- **Solution**: 
  - Check browser permissions
  - Use HTTPS in production
  - Try different browser (Chrome recommended)

### Check-in Not Working
- **Issue**: Manual check-in fails
- **Solution**:
  - Verify user has correct role
  - Check registration status (must be "confirmed")
  - Check browser console for errors

### Stats Not Updating
- **Issue**: Statistics don't refresh
- **Solution**:
  - Check network connection
  - Verify API endpoint is accessible
  - Refresh page manually

### Login Issues
- **Issue**: Can't login to staff portal
- **Solution**:
  - Verify user role is 'staff', 'organizer', or 'admin'
  - Check credentials
  - Ensure migrations are applied

## Future Enhancements

### Planned Features
1. **Event Team Assignments**
   - Assign specific staff to specific events
   - Staff only see their assigned events

2. **Offline Mode**
   - Cache registrations locally
   - Sync check-ins when online

3. **Badge Printing**
   - Print badges on check-in
   - Thermal printer support

4. **Multi-language Support**
   - Internationalization
   - Language selection

5. **Advanced Analytics**
   - Check-in trends
   - Peak time analysis
   - Staff performance metrics

6. **Push Notifications**
   - Alert staff of issues
   - Event start reminders

## Testing

### Create Test Data
```python
python manage.py shell

from events.models import Event
from registration.models import Registration, TicketType
from users.models import User
from django.utils import timezone

# Create test event
event = Event.objects.create(
    title="Test Event",
    start_date=timezone.now().date(),
    organizer=User.objects.filter(role='organizer').first()
)

# Create ticket type
ticket = TicketType.objects.create(
    event=event,
    name="General Admission",
    price=0,
    quantity_available=100,
    sales_start=timezone.now(),
    sales_end=timezone.now() + timezone.timedelta(days=30)
)

# Create test registrations
for i in range(10):
    Registration.objects.create(
        event=event,
        ticket_type=ticket,
        attendee_name=f"Test Attendee {i+1}",
        attendee_email=f"attendee{i+1}@test.com",
        status='confirmed'
    )
```

### Test QR Codes
Each registration has a unique QR code stored in `registration.qr_code`. You can:
1. Generate QR code images using the registration success page
2. Display QR codes on mobile devices
3. Test scanning with the staff portal

## Support

For issues or questions:
1. Check this guide first
2. Review Django logs
3. Check browser console for JavaScript errors
4. Verify API endpoints are working

## Summary

The Gate Staff Portal provides a streamlined, mobile-first solution for event check-in management. With QR code scanning, manual check-in options, and real-time statistics, gate staff can efficiently manage attendee entry while maintaining security and audit trails.

**Key Benefits:**
- ✅ Fast check-in process
- ✅ Mobile-responsive design
- ✅ Real-time statistics
- ✅ Secure role-based access
- ✅ Easy to use interface
- ✅ Audit trail for all check-ins
