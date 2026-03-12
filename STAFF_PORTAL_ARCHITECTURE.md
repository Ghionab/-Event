# Gate Staff Portal - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Event Management System                       │
│                      Three-Portal Architecture                   │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Organizer       │  │  Participant     │  │  Gate Staff      │
│  Portal          │  │  Portal          │  │  Portal          │
│  Port 8000       │  │  Port 8001       │  │  Port 8002 ✨    │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ • Event Mgmt     │  │ • Registration   │  │ • QR Scanner     │
│ • Analytics      │  │ • Browse Events  │  │ • Check-in       │
│ • Reports        │  │ • My Tickets     │  │ • Live Stats     │
│ • Settings       │  │ • Profile        │  │ • Attendee List  │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                      │
         └─────────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Django Backend    │
                    │   (Shared Database) │
                    └─────────────────────┘
```

## Portal Comparison

| Feature              | Organizer (8000) | Participant (8001) | Staff (8002) |
|---------------------|------------------|-------------------|--------------|
| Event Management    | ✅ Full          | ❌ View Only      | ❌ View Only |
| Registration        | ✅ Manage        | ✅ Self Register  | ❌ No        |
| Check-in            | ✅ Manual        | ❌ No             | ✅ QR + Manual |
| QR Scanner          | ❌ No            | ❌ No             | ✅ Yes       |
| Analytics           | ✅ Full          | ❌ No             | ✅ Basic     |
| User Roles          | Admin, Organizer | Attendee          | Staff        |
| Mobile Optimized    | ⚠️ Partial       | ✅ Yes            | ✅ Yes       |

## Staff Portal Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gate Staff Portal (8002)                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Login      │  │  Event List  │  │  Dashboard   │      │
│  │   Page       │  │   (Active)   │  │  (Scanner)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  Components:                                                  │
│  • Bootstrap 5 UI                                            │
│  • html5-qrcode Scanner                                      │
│  • JavaScript (Vanilla)                                      │
│  • Font Awesome Icons                                        │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ AJAX/Fetch API
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      Backend Layer                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              staff/views.py                           │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ • event_list()        - Show active events           │  │
│  │ • event_dashboard()   - Main check-in interface      │  │
│  │ • manual_checkin()    - Manual check-in API          │  │
│  │ • checkin_stats()     - Real-time statistics         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           staff/decorators.py                         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ • @staff_required     - Role-based access control    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Django ORM
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                       Data Layer                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  User    │  │  Event   │  │Registration│ │ CheckIn  │   │
│  │  Model   │  │  Model   │  │   Model    │ │  Model   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
│  Database: SQLite (Dev) / PostgreSQL (Prod)                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Check-in Flow

### QR Code Check-in Flow

```
┌──────────────┐
│ Staff Opens  │
│  Dashboard   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Click "Start │
│  Scanning"   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Camera Opens │
│ (html5-qrcode)│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Scan QR Code │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ JavaScript: onScanSuccess()          │
│ 1. Extract QR code data              │
│ 2. Find registration by QR code      │
│ 3. Call check-in API                 │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ API: POST /api/v1/events/{id}/       │
│      registrations/{id}/check-in/    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Backend: registration.check_in()     │
│ 1. Validate status (must be confirmed)│
│ 2. Update status to 'checked_in'    │
│ 3. Set checked_in_at timestamp      │
│ 4. Set checked_in_by user           │
│ 5. Create CheckIn log entry         │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Response: Success or Error           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ UI Update:                           │
│ • Show success/error alert           │
│ • Update registration card           │
│ • Refresh statistics                 │
│ • Resume scanner after 2 seconds     │
└──────────────────────────────────────┘
```

### Manual Check-in Flow

```
┌──────────────┐
│ Staff Searches│
│  for Attendee │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Click "Check │
│   In" Button │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Confirmation │
│    Dialog    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ JavaScript: manualCheckin()          │
│ POST /staff/checkin/{id}/            │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Backend: manual_checkin()            │
│ 1. Get registration                  │
│ 2. Validate status                   │
│ 3. Call registration.check_in()      │
│ 4. Create CheckIn log (method='manual')│
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Response: JSON with success/error    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ UI Update:                           │
│ • Show success alert                 │
│ • Update card to "checked-in" style  │
│ • Disable check-in button            │
│ • Refresh statistics                 │
└──────────────────────────────────────┘
```

## Authentication Flow

```
┌──────────────┐
│ Access       │
│ localhost:8002│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Redirect to  │
│ /staff/login/│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Enter Email  │
│ & Password   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Django Authentication                │
│ 1. Validate credentials              │
│ 2. Check user.role                   │
└──────┬───────────────────────────────┘
       │
       ├─── Role = 'staff' ────────────┐
       │                               │
       ├─── Role = 'organizer' ────────┤
       │                               │
       ├─── Role = 'admin' ────────────┤
       │                               │
       └─── Other roles ───────────────┤
                                       │
                                       ▼
                              ┌──────────────┐
                              │ Access Denied│
                              │ Redirect to  │
                              │    Login     │
                              └──────────────┘
       │
       ▼
┌──────────────┐
│ Create Session│
│ (8 hours)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Redirect to  │
│ /staff/events/│
└──────────────┘
```

## Data Models

```
┌─────────────────────────────────────────────────────────────┐
│                         User Model                           │
├─────────────────────────────────────────────────────────────┤
│ • email (unique)                                             │
│ • role: ['admin', 'organizer', 'staff', 'speaker',          │
│          'sponsor', 'attendee']                              │
│ • first_name, last_name                                      │
│ • is_active, is_staff, is_superuser                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        Event Model                           │
├─────────────────────────────────────────────────────────────┤
│ • title, description                                         │
│ • start_date, end_date                                       │
│ • venue_name, venue_address                                  │
│ • organizer (FK → User)                                      │
│ • status: ['draft', 'published', 'cancelled']               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Registration Model                        │
├─────────────────────────────────────────────────────────────┤
│ • event (FK → Event)                                         │
│ • user (FK → User, nullable)                                 │
│ • ticket_type (FK → TicketType)                             │
│ • registration_number (unique)                               │
│ • status: ['pending', 'confirmed', 'cancelled',             │
│            'waitlisted', 'checked_in', 'refunded']          │
│ • attendee_name, attendee_email, attendee_phone             │
│ • qr_code (unique, 16 chars)                                │
│ • checked_in_at (timestamp)                                  │
│ • checked_in_by (FK → User)                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      CheckIn Model                           │
├─────────────────────────────────────────────────────────────┤
│ • registration (FK → Registration)                           │
│ • checked_in_by (FK → User)                                  │
│ • check_in_time (auto_now_add)                              │
│ • method: ['qr_scan', 'manual', 'kiosk', 'self']           │
│ • location, device_info                                      │
│ • notes                                                      │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
event_project/
├── event_project/
│   ├── settings.py              # Base settings (Port 8000)
│   ├── settings_participant.py  # Participant settings (Port 8001)
│   ├── settings_staff.py        # Staff settings (Port 8002) ✨
│   ├── urls.py                  # Organizer URLs
│   ├── urls_participant.py      # Participant URLs
│   └── urls_staff.py            # Staff URLs ✨
│
├── staff/                       # Staff app ✨
│   ├── templates/
│   │   └── staff/
│   │       ├── base.html
│   │       ├── login.html
│   │       ├── event_list.html
│   │       └── event_dashboard.html
│   ├── views.py
│   ├── decorators.py
│   ├── urls.py
│   └── apps.py
│
├── users/
│   └── models.py                # Updated with STAFF role ✨
│
├── registration/
│   └── models.py                # Registration, CheckIn models
│
├── events_api/
│   └── views/
│       └── registration_views.py # Check-in API endpoint
│
├── run_staff_portal.py          # Quick start script ✨
├── test_staff_portal.py         # Setup verification ✨
├── STAFF_PORTAL_GUIDE.md        # Complete guide ✨
├── STAFF_PORTAL_COMMANDS.md     # Command reference ✨
├── STAFF_PORTAL_SUMMARY.md      # Implementation summary ✨
└── STAFF_PORTAL_ARCHITECTURE.md # This file ✨
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Stack                          │
├─────────────────────────────────────────────────────────────┤
│ • HTML5                                                      │
│ • CSS3 (Custom + Bootstrap)                                  │
│ • JavaScript (Vanilla ES6+)                                  │
│ • Bootstrap 5.3.0                                            │
│ • Font Awesome 6.4.0                                         │
│ • html5-qrcode 2.3.8                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Backend Stack                           │
├─────────────────────────────────────────────────────────────┤
│ • Django 6.0.1                                               │
│ • Python 3.12+                                               │
│ • Django REST Framework                                      │
│ • SQLite (Dev) / PostgreSQL (Prod)                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Security & Auth                           │
├─────────────────────────────────────────────────────────────┤
│ • Django Session Authentication                              │
│ • CSRF Protection                                            │
│ • Role-Based Access Control                                  │
│ • HTTP-Only Cookies                                          │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Setup                          │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │ Load Balancer│
                    │   (Nginx)    │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼─────┐  ┌──────▼─────┐  ┌──────▼─────┐
    │ Organizer  │  │Participant │  │   Staff    │
    │   :8000    │  │   :8001    │  │   :8002    │
    └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                    ┌──────▼───────┐
                    │  PostgreSQL  │
                    │   Database   │
                    └──────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Security Layers                         │
└─────────────────────────────────────────────────────────────┘

Layer 1: Network
├── HTTPS/TLS encryption
├── Firewall rules
└── Rate limiting

Layer 2: Application
├── Django middleware
├── CSRF protection
├── Session management
└── CORS configuration

Layer 3: Authentication
├── Login required
├── Password hashing (PBKDF2)
└── Session timeout (8 hours)

Layer 4: Authorization
├── Role-based access (@staff_required)
├── Permission checks
└── User attribution

Layer 5: Data
├── SQL injection protection (ORM)
├── XSS protection (template escaping)
└── Audit logs (CheckIn model)
```

## Performance Optimization

```
┌─────────────────────────────────────────────────────────────┐
│                   Performance Features                       │
└─────────────────────────────────────────────────────────────┘

Frontend:
├── Minimal JavaScript (no heavy frameworks)
├── CDN for libraries (Bootstrap, Font Awesome)
├── Lazy loading for QR scanner
├── Debounced search
└── Optimized images

Backend:
├── Database query optimization
│   ├── select_related() for ForeignKeys
│   ├── prefetch_related() for M2M
│   └── Indexed fields (qr_code, registration_number)
├── Caching (Django cache framework)
└── Pagination for large lists

API:
├── Minimal response payloads
├── Gzip compression
└── Connection pooling
```

This architecture provides a scalable, secure, and maintainable solution for event check-in management.
