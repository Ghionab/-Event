# Event Creation Updates

## Changes Made

### 1. Removed Status Field from Event Creation Form

The `status` field has been removed from the event creation form. When creating a new event, the status is now automatically set to `'draft'`.

**Why?** This simplifies the event creation process and ensures consistency - all new events start as drafts and can be published later.

**Implementation:**
- Removed `'status'` from `EventForm.Meta.fields` in `events/forms.py`
- Added automatic status assignment in `event_create` view: `event.status = 'draft'`
- Updated API serializer to exclude status from creation and auto-assign draft status

### 2. Added Email Invitation Functionality

Event organizers can now send invitation emails when creating an event.

**Features:**
- New `invite_emails` field in the event creation form
- Accepts comma-separated or newline-separated email addresses
- Validates each email address
- Sends personalized invitation emails to all provided addresses
- Shows success message with count of sent invitations

**Implementation:**
- Added `invite_emails` field to `EventForm` with validation
- Created `send_event_invitations()` helper function in `events/views.py`
- Email includes:
  - Event title and description
  - Date, time, and location
  - Registration link
  - Organizer information

**Email Configuration:**
The system uses Django's email backend. For development, emails are printed to the console. For production, configure SMTP settings in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

## Testing

Run the tests to verify the changes:

```bash
python manage.py test events.tests.EventViewsTest.test_event_create_auto_draft_status
python manage.py test events.tests.EventViewsTest.test_event_create_with_email_invitations
```

## Usage

1. Navigate to the event creation page
2. Fill in the event details (status field is no longer visible)
3. Optionally, add email addresses in the "Invite via Email" field
4. Submit the form
5. The event will be created with draft status
6. If emails were provided, invitations will be sent automatically

## Files Modified

- `events/forms.py` - Updated EventForm to remove status and add invite_emails
- `events/views.py` - Updated event_create view and added send_event_invitations function
- `events_api/serializers/event_serializers.py` - Updated EventCreateSerializer
- `events/tests.py` - Added tests for new functionality
