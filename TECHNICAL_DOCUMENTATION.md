# Event Management System - Technical Documentation

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Database Models](#4-database-models)
5. [URL Routing](#5-url-routing)
6. [Authentication System](#6-authentication-system)
7. [API Endpoints](#7-api-endpoints)
8. [Two-Portal Architecture](#8-two-portal-architecture)
9. [Settings Configuration](#9-settings-configuration)
10. [Middleware & Custom Components](#10-middleware--custom-components)
11. [Running the Application](#11-running-the-application)

---

## 1. Project Overview

This is a comprehensive **Django-based Event Management System** with a **two-portal architecture**:

- **Organizer Portal** (Port 8000): For event organizers to create and manage events
- **Participant Portal** (Port 8001): For attendees to discover and register for events

### Key Features
- Multi-role user system (Admin, Organizer, Speaker, Sponsor, Attendee)
- Complete event lifecycle management
- Registration with multiple ticket types and promo codes
- QR code check-in system with badges
- Communication tools (email, SMS, polls, Q&A)
- Business analytics and reporting
- REST API with Swagger documentation

---

## 2. Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 6.0.1 |
| Database | SQLite3 (db.sqlite3) |
| API | Django REST Framework |
| API Documentation | drf-spectacular (Swagger/OpenAPI) |
| CORS | django-cors-headers |
| Authentication | Session-based with custom User model |
| Frontend | Django Templates + Tailwind CSS |

### Python Dependencies
```
Django>=6.0.1
djangorestframework
django-cors-headers
drf-spectacular
```

---

## 3. Project Structure

```
Event Managment/
├── event_project/              # Django project settings
│   ├── __init__.py
│   ├── settings.py            # Main settings (Organizer)
│   ├── settings_participant.py # Participant portal settings
│   ├── urls.py                # Main URL config
│   ├── urls_participant.py    # Participant URLs
│   ├── wsgi.py
│   ├── middleware.py          # Custom middleware
│   └── ...
├── events/                    # Core event management
├── users/                     # Custom user model
├── registration/              # Tickets, registrations, check-in
├── organizers/                # Organizer portal
├── communication/             # Email, SMS, polls, Q&A
├── business/                 # Sponsors, analytics, invoices
├── advanced/                 # Vendors, contracts, tasks
├── events_api/               # REST API
├── templates/                # Django templates
│   ├── participant/          # Participant portal templates
│   └── ...
└── manage.py                 # Django management script
```

### Installed Apps

| App | Purpose |
|-----|---------|
| `events` | Core event management - events, sessions, speakers, tracks, rooms, sponsors |
| `users` | Custom user model with role-based access |
| `registration` | Ticket management, registrations, check-in, badges |
| `organizers` | Organizer portal - dashboard, analytics, team management |
| `communication` | Email/SMS/push notifications, live polls, Q&A |
| `business` | Sponsor management, analytics, financials, invoices |
| `advanced` | Vendors, contracts, team collaboration, tasks |
| `events_api` | REST API endpoints |

---

## 4. Database Models

### 4.1 Users App (`users/models.py`)

**Custom User Model**:
```python
class User(AbstractUser):
    email = models.EmailField(unique=True)  # Primary identifier
    role = models.CharField(choices=UserRole.choices)
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    notification_preferences = models.JSONField(default=dict)
```

**User Roles**:
- `ADMIN` - System administrator
- `ORGANIZER` - Event organizer
- `SPEAKER` - Event speaker
- `SPONSOR` - Event sponsor
- `ATTENDEE` - Event attendee

### 4.2 Events App (`events/models.py`)

| Model | Key Fields |
|-------|------------|
| **Event** | title, slug, description, event_type (IN_PERSON/VIRTUAL/HYBRID), status, start_date, end_date, venue_name, city, primary_color, max_attendees, organizer |
| **Speaker** | name, email, bio, photo, company, job_title, social_links, is_confirmed, is_featured |
| **Track** | name, description, color, event |
| **EventSession** | title, description, start_time, end_time, session_type, capacity, track, room, speakers |
| **Room** | name, capacity, amenities, virtual_url, event |
| **Sponsor** | name, tier (platinum/gold/silver/bronze), logo, website, description, event |

### 4.3 Registration App (`registration/models.py`)

| Model | Key Fields |
|-------|------------|
| **TicketType** | name, event, price, quantity_available, sales_start, sales_end, benefits |
| **PromoCode** | code, discount_type, discount_value, max_uses, valid_from, valid_until, event |
| **Registration** | event, user, ticket_type, status, qr_code, checked_in_at, custom_fields |
| **RegistrationField** | field_name, field_type (includes 'file' type), label, required, options |
| **RegistrationDocument** | registration, field, file, original_filename, file_size, is_validated |
| **Badge** | registration, badge_type, qr_code, printed |
| **CheckIn** | registration, method (qr_scan/manual/kiosk), checked_in_by |
| **AttendeePreference** | user, event, dietary_requirements, accessibility_needs, networking |
| **SessionAttendance** | registration, session, rating, feedback |

### 4.4 Organizers App (`organizers/models.py`)

| Model | Key Fields |
|-------|------------|
| **OrganizerProfile** | user, company_name, website, logo, description, verified, subscription_plan |
| **OrganizerTeamMember** | profile, user, role, permissions |
| **EventAnalytics** | event, views, registrations, revenue, tickets_sold |

### 4.5 Communication App (`communication/models.py`)

| Model | Key Fields |
|-------|------------|
| **EmailTemplate** | name, subject, body, event |
| **LivePoll** | question, poll_type, session, is_active |
| **LiveQA** | question, user, session, upvotes, is_approved |

### 4.6 Business App (`business/models.py`)

| Model | Key Fields |
|-------|------------|
| **Invoice** | event, sponsor, amount, status, due_date |
| **Expense** | event, category, amount, description, date |
| **Budget** | event, total_amount, spent_amount |

### 4.7 Advanced App (`advanced/models.py`)

| Model | Key Fields |
|-------|------------|
| **Vendor** | name, category, contact_email, phone |
| **Contract** | vendor, event, terms, status, signed_date |
| **Task** | title, event, assigned_to, status, priority, due_date |
| **AuditLog** | user, action, model, changes, timestamp |

---

## 5. URL Routing

### 5.1 Main URL Configuration (`event_project/urls.py`)

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/organizers/login/', permanent=False)),
    path('events/', include('events.urls')),
    path('users/', include('users.urls')),
    path('registration/', include('registration.urls')),
    path('organizers/', include('organizers.urls')),
    path('communication/', include('communication.urls')),
    path('business/', include('business.urls')),
    path('advanced/', include('advanced.urls')),
    path('accounts/login/', auth_views.LoginView.as_view()),
    path('accounts/logout/', auth_views.LogoutView.as_view()),
    path('api/v1/', include('events_api.urls')),
    path('api/schema/', SpectacularAPIView.as_view()),
    path('api/docs/', SpectacularSwaggerView.as_view()),
]
```

### 5.2 Organizer Portal URLs

| URL | View | Description |
|-----|------|-------------|
| `/organizers/login/` | `organizer_login` | Organizer login |
| `/organizers/dashboard/` | `dashboard` | Dashboard overview |
| `/organizers/events/` | `event_list` | List organizer's events |
| `/organizers/events/create/` | `event_create` | Create new event |
| `/organizers/events/<id>/` | `event_detail` | Event details |
| `/organizers/events/<id>/edit/` | `event_edit` | Edit event |
| `/organizers/analytics/` | `analytics` | View analytics |
| `/organizers/team/` | `team_members` | Manage team |
| `/organizers/settings/` | `settings` | Organizer settings |

### 5.3 Participant Portal URLs (`urls_participant.py`)

| URL | View | Description |
|-----|------|-------------|
| `/` | `participant_home` | Home page |
| `/events/` | `participant_events` | Event listing |
| `/events/<id>/` | `participant_event_detail` | Event details |
| `/events/<id>/register/` | `participant_register` | Register for event |
| `/login/` | `participant_login` | User login |
| `/register/` | `participant_signup` | User registration |
| `/my-registrations/` | `participant_my_registrations` | User's registrations |

---

## 6. Authentication System

### 6.1 Custom User Model

Located in `users/models.py`:
- Extends `AbstractUser`
- Uses `email` as the primary identifier (username removed)
- Custom `UserManager` with `create_user()` and `create_superuser()` methods

### 6.2 Authentication Configuration

```python
# settings.py
AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'events_api.authentication.CsrfExemptSessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}
```

### 6.3 Custom Authentication Class

```python
# events_api/authentication/__init__.py
class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Custom authentication that exempts CSRF for API endpoints
    while maintaining session security
    """
    def enforce_csrf(self, request):
        return  # Skip CSRF check
```

### 6.4 Decorators

- `@login_required` - Django's built-in decorator
- `@organizer_required` - Custom decorator ensuring user has organizer profile
- `@csrf_exempt` - For public API endpoints

---

## 7. API Endpoints

### 7.1 Authentication Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/v1/auth/login/` | User login |
| POST | `/api/v1/auth/logout/` | User logout |
| GET | `/api/v1/auth/user/` | Get current user |
| POST | `/api/v1/auth/register/` | Register new user |

### 7.2 Event Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/events/` | List events |
| POST | `/api/v1/events/` | Create event |
| GET | `/api/v1/events/{id}/` | Get event details |
| PUT | `/api/v1/events/{id}/` | Update event |
| DELETE | `/api/v1/events/{id}/` | Delete event |

### 7.3 Event-Related Resources

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/v1/events/{id}/tracks/` | Tracks |
| GET/POST | `/api/v1/events/{id}/rooms/` | Rooms |
| GET/POST | `/api/v1/events/{id}/sponsors/` | Sponsors |
| GET/POST | `/api/v1/events/{id}/speakers/` | Speakers |
| GET/POST | `/api/v1/events/{id}/sessions/` | Sessions |
| GET/POST | `/api/v1/events/{id}/tickets/` | Ticket types |
| GET/POST | `/api/v1/events/{id}/promocodes/` | Promo codes |

### 7.4 Registration Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/v1/events/{id}/registrations/` | Registrations |
| POST | `/api/v1/events/{id}/registrations/{id}/cancel/` | Cancel registration |
| POST | `/api/v1/events/{id}/registrations/{id}/check-in/` | Check-in |

### 7.5 Public Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/public/events/` | Public event listing |
| POST | `/api/v1/register/` | Public registration (no auth) |

### 7.6 API Documentation

- Swagger UI: `/api/docs/`
- OpenAPI Schema: `/api/schema/`

---

## 8. Two-Portal Architecture

### 8.1 Overview

The system uses **two separate Django settings** to run on different ports:

| Portal | Port | Settings Module | URL Config |
|--------|------|-----------------|------------|
| Organizer | 8000 | `event_project.settings` | `event_project.urls` |
| Participant | 8001 | `event_project.settings_participant` | `event_project.urls_participant` |

### 8.2 Organizer Portal (Port 8000)

**Purpose**: For event organizers to manage their events

**Key Features**:
- Event creation and editing
- Dashboard with analytics
- Team management
- Ticket management
- Attendee management
- Check-in system

**Access**: Redirects unauthenticated users to `/organizers/login/`

### 8.3 Participant Portal (Port 8001)

**Purpose**: For attendees to discover and register for events

**Key Features**:
- Browse public events
- User registration/login
- Event registration
- View my registrations
- QR code badge display
- Session feedback

**Access**: Public access to event listings, authentication required for registration

### 8.4 Running Both Portals

```bash
# Terminal 1 - Organizer Portal
python manage.py runserver 8000 --settings=event_project.settings

# Terminal 2 - Participant Portal
python manage.py runserver 8001 --settings=event_project.settings_participant
```

Or use the batch files:
```bash
run_organizer.bat   # Starts on port 8000
run_participant.bat # Starts on port 8001
```

---

## 9. Settings Configuration

### 9.1 Main Settings (`settings.py`)

Key configurations for the Organizer Portal:

```python
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'events', 'users', 'registration', 'organizers',
    'communication', 'business', 'advanced', 'events_api',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'users.User'
```

### 9.2 Participant Settings (`settings_participant.py`)

```python
# Inherits from settings.py with overrides:
DEBUG = True
SECRET_KEY = 'participant-secret-key-change-in-production'
ALLOWED_HOSTS = ['*']

ROOT_URLCONF = 'event_project.urls_participant'

# Simplified middleware (no CSRF for API)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'event_project.middleware.DisableCSRFMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8001",
    "http://localhost:3000",
]
```

---

## 10. Middleware & Custom Components

### 10.1 Custom Middleware (`middleware.py`)

```python
class DisableCSRFMiddleware:
    """
    Middleware to disable CSRF for specific endpoints
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip CSRF check for registration API
        if request.path == '/api/v1/register/' and request.method == 'POST':
            request._dont_enforce_csrf_checks = True

        response = self.get_response(request)
        return response
```

### 10.2 Middleware Stack

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 10.3 Third-Party Integrations

| Package | Purpose |
|---------|---------|
| `django-cors-headers` | Cross-origin request handling |
| `djangorestframework` | REST API framework |
| `drf-spectacular` | OpenAPI/Swagger documentation |

---

## 11. Document Upload Feature

### 11.1 Overview

The system supports file uploads for pre-registration forms, allowing organizers to collect various document types (PDF, Excel, Word, images) from attendees during registration.

### 11.2 Supported File Types

| Category | Extensions | MIME Types |
|----------|------------|------------|
| PDF | `.pdf` | application/pdf |
| Word | `.doc`, `.docx` | application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| Excel | `.xls`, `.xlsx`, `.csv` | application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, text/csv |
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` | image/jpeg, image/png, image/gif, image/webp |
| Archives | `.zip`, `.rar` | application/zip, application/x-rar-compressed |
| Text | `.txt`, `.rtf` | text/plain, application/rtf |

### 11.3 File Upload Settings (`settings.py`)

```python
# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# Allowed file extensions for document uploads
ALLOWED_FILE_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv',
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.zip', '.rar', '.txt', '.rtf'
]

# Max file size for uploads (in bytes) - default 10MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

# Media files (Uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 11.4 RegistrationDocument Model

```python
class RegistrationDocument(models.Model):
    """Uploaded documents for pre-registration (PDF, Excel, etc.)"""
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    field = models.ForeignKey(RegistrationField, on_delete=models.CASCADE)

    # Document details
    file = models.FileField(upload_to='registration_documents/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # Size in bytes
    mime_type = models.CharField(max_length=100, blank=True)

    # Validation status
    is_validated = models.BooleanField(default=False)
    validation_notes = models.TextField(blank=True)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
```

### 11.5 RegistrationField - File Type

The `RegistrationField` model includes a 'file' field type:

```python
FIELD_TYPES = [
    ...
    ('file', 'File Upload'),
]
```

Organizers can configure file upload fields with custom allowed extensions:
- Example options: `.pdf,.doc,.xlsx` (comma-separated)

### 11.6 Document Upload Views

| View | URL | Description |
|------|-----|-------------|
| `document_list` | `/registration/<id>/documents/` | List all uploaded documents |
| `document_detail` | `/registration/documents/<id>/` | View document details |
| `document_validate` | `/registration/documents/<id>/validate/` | Validate/reject document (organizer) |
| `document_download` | `/registration/documents/<id>/download/` | Download document |
| `document_delete` | `/registration/documents/<id>/delete/` | Delete document (owner only) |
| `documents_api` | `/registration/<id>/documents/api/` | REST API for documents |

### 11.7 Document Upload Flow

1. **Organizer creates file field**: In event setup, organizer adds a custom registration field with type "File Upload" and specifies allowed file extensions.

2. **Attendee uploads file**: During registration, attendee sees file upload input and can upload files matching the allowed types.

3. **File validation**: System validates:
   - File size (max 10MB)
   - File extension matches allowed list
   - MIME type is correct

4. **Document storage**: Files are stored in `media/registration_documents/YYYY/MM/`

5. **Document review**: Organizers can view, validate (approve/reject), and download uploaded documents.

### 11.8 API Endpoints for Documents

```bash
# List documents for a registration
GET /registration/<registration_id>/documents/api/

# Upload a new document
POST /registration/<registration_id>/documents/api/

# Delete a document
DELETE /registration/<registration_id>/documents/api/?document_id=<id>
```

---

---

## 12. Bulk Registration Feature

### 12.1 Overview

The system supports bulk registration through Excel/CSV file uploads, allowing organizers to register multiple attendees at once.

### 12.2 BulkRegistrationUpload Model

```python
class BulkRegistrationUpload(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='bulk_registrations/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    status = models.CharField(choices=STATUS_CHOICES, default='pending')
    total_rows = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)
```

### 12.3 BulkRegistrationRow Model

```python
class BulkRegistrationRow(models.Model):
    bulk_upload = models.ForeignKey(BulkRegistrationUpload)
    row_number = models.IntegerField()
    row_data = models.JSONField(default=dict)
    registration = models.OneToOneField(Registration)
    status = models.CharField(choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
```

### 12.4 ManualRegistration Model

```python
class ManualRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    attendee_name = models.CharField(max_length=255)
    attendee_email = models.EmailField()
    attendee_phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255, blank=True)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.SET_NULL, null=True)
    registration = models.OneToOneField(Registration, null=True)
    status = models.CharField(choices=STATUS_CHOICES, default='draft')
```

### 12.5 Bulk Registration Flow

1. **Upload File**: Organizer uploads Excel (.xlsx) or CSV file
2. **File Processing**: System reads rows and validates data
3. **Row Processing**: Each row creates a registration or logs errors
4. **Email Notifications**: Optional invitation emails sent to attendees

### 12.6 Expected File Format

| Column | Required | Description |
|--------|----------|-------------|
| name | Yes | Full name of attendee |
| email | Yes | Email address |
| phone | No | Phone number |
| company | No | Company name |
| job_title | No | Job title |

### 12.7 Bulk Registration URLs

| View | URL | Description |
|------|-----|-------------|
| `bulk_registration_upload` | `/registration/bulk/upload/<event_id>/` | Upload bulk file |
| `bulk_registration_list` | `/registration/bulk/list/<event_id>/` | List all uploads |
| `bulk_registration_detail` | `/registration/bulk/<bulk_id>/` | View upload details |
| `manual_registration_create` | `/registration/manual/create/<event_id>/` | Manual entry form |
| `manual_registration_list` | `/registration/manual/list/<event_id>/` | List manual entries |

### 12.8 Supported File Types

- Excel (.xlsx)
- Excel (.xls)
- CSV (.csv)

Maximum file size: 5MB

---

## 13. QR Code System

### 13.1 Overview

Each registration automatically generates a unique QR code for check-in purposes.

### 13.2 QR Code Generation

QR codes are automatically generated when a registration is created:

```python
def save(self, *args, **kwargs):
    if not self.registration_number:
        self.registration_number = f"REG-{uuid.uuid4().hex[:8].upper()}"
    if not self.qr_code:
        self.qr_code = str(uuid.uuid4().hex[:16])
    super().save(*args, **kwargs)
```

### 13.3 QR Code Methods

```python
# Generate QR code image (base64)
qr_image = registration.generate_qr_code_image()

# Get check-in status
status = registration.get_check_in_status()
```

### 13.4 QR Code Management Views

| View | URL | Description |
|------|-----|-------------|
| `qr_code_list` | `/registration/qr/<event_id>/` | List all QR codes |
| `qr_code_download` | `/registration/qr/<id>/download/` | Download QR code image |
| `qr_code_print` | `/registration/qr/<event_id>/print/` | Print all QR codes |
| `qr_code_send_emails` | `/registration/qr/<event_id>/send-emails/` | Send QR codes via email |

### 13.5 Check-in Management Views

| View | URL | Description |
|------|-----|-------------|
| `qr_check_in` | `/registration/check-in/qr/` | QR code scan check-in |
| `manual_check_in` | `/registration/check-in/manual/<event_id>/` | Manual check-in |
| `perform_check_in` | `/registration/check-in/<id>/` | Perform check-in |
| `checkin_analytics` | `/registration/check-in/analytics/<event_id>/` | Check-in analytics |
| `checkin_history` | `/registration/check-in/history/<event_id>/` | Check-in history |
| `checkin_undo` | `/registration/check-in/undo/<id>/` | Undo check-in |

### 13.6 Check-in Flow

1. **QR Code Generation**: Auto-generated when registration is created
2. **QR Display**: Attendee shows QR code on mobile or printed badge
3. **Scanning**: Organizer scans QR code using `/check-in/qr/` endpoint
4. **Validation**: System validates QR code and checks registration status
5. **Check-in**: Registration status updated to "checked_in"
6. **Logging**: Check-in is logged with timestamp and method

### 13.7 QR Code Data Format

QR code contains: `A1B2C3D4E5F6` (16-character unique code)

Example check-in URL:
```
POST /registration/check-in/qr/?qr=A1B2C3D4E5F6
```

### 13.8 Check-in Methods

| Method | Description |
|--------|-------------|
| `qr_scan` | QR code scanned via camera |
| `manual` | Manual entry by staff |
| `kiosk` | Self-service kiosk |
| `self` | Self check-in via app |

---

## 14. Running the Application

### 11.1 Prerequisites

1. Python 3.14+
2. Virtual environment activated
3. Dependencies installed:
   ```bash
   pip install Django djangorestframework django-cors-headers drf-spectacular
   ```

### 11.2 Database Setup

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run the development servers
```

### 11.3 Starting Both Portals

**Option 1: Using manage.py with --settings flag**

```bash
# Terminal 1 - Organizer Portal (port 8000)
python manage.py runserver 8000 --settings=event_project.settings

# Terminal 2 - Participant Portal (port 8001)
python manage.py runserver 8001 --settings=event_project.settings_participant
```

**Option 2: Using batch files**

```bash
# Run both terminals
run_organizer.bat
run_participant.bat
```

### 11.4 Access URLs

| Portal | URL |
|--------|-----|
| Organizer Admin | http://localhost:8000/admin/ |
| Organizer Login | http://localhost:8000/organizers/login/ |
| Participant Home | http://localhost:8001/ |
| Participant Events | http://localhost:8001/events/ |
| API Docs | http://localhost:8000/api/docs/ |

---

## 13. Development Notes

### 12.1 Key Files to Know

| File | Purpose |
|------|---------|
| `manage.py` | Django management script |
| `event_project/settings.py` | Main settings |
| `event_project/settings_participant.py` | Participant portal settings |
| `event_project/urls.py` | Main URL configuration |
| `event_project/urls_participant.py` | Participant URLs |
| `event_project/middleware.py` | Custom middleware |

### 12.2 Common Tasks

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test

# Check system
python manage.py check
```

### 12.3 Code Style

- Follows Django conventions
- Uses Tailwind CSS for frontend styling
- REST API follows DRF best practices
- OpenAPI schema generated via drf-spectacular

---

## Appendix: Database Schema Overview

```
User (users_user)
├── id, email, password, role, is_verified
│
├── OrganizerProfile (organizers_organizerprofile)
│   ├── user_id -> User
│   ├── company_name, website, logo
│   └── verified, subscription_plan
│
├── Event (events_event)
│   ├── id, title, slug, description
│   ├── organizer_id -> User
│   ├── status (draft/published/ongoing/completed/cancelled)
│   ├── start_date, end_date
│   └── venue_name, city, primary_color
│
├── TicketType (registration_tickettype)
│   ├── event_id -> Event
│   ├── name, price, quantity_available
│   └── sales_start, sales_end
│
├── Registration (registration_registration)
│   ├── event_id -> Event
│   ├── user_id -> User
│   ├── ticket_type_id -> TicketType
│   ├── status, qr_code, checked_in_at
│   └── custom_fields (JSON)
│
├── EventSession (events_eventsession)
│   ├── event_id -> Event
│   ├── title, description
│   ├── start_time, end_time
│   ├── session_type, capacity
│   ├── track_id -> Track
│   └── room_id -> Room
│
├── Speaker (events_speaker)
│   ├── event_id -> Event
│   ├── name, email, bio, photo
│   └── is_confirmed, is_featured
│
└── Sponsor (events_sponsor)
    ├── event_id -> Event
    ├── name, tier, logo, website
    └── description
```

---

*Last Updated: February 2026*
*Version: 1.0*
