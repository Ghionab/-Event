# Quick Reference Guide

## For Developers

### What Changed?
1. **Status field removed** from event creation form
2. **Email invitations** added to event creation

### Key Files Modified
```
events/
├── forms.py              # Added invite_emails field, removed status
├── views.py              # Added send_event_invitations() function
├── tests.py              # Added test coverage
└── templates/
    └── events/
        └── event_form.html   # Updated layout

events_api/
└── serializers/
    └── event_serializers.py  # Removed status from creation
```

### Testing
```bash
# Run all event tests
python manage.py test events

# Run specific tests
python manage.py test events.tests.EventViewsTest.test_event_create_auto_draft_status
python manage.py test events.tests.EventViewsTest.test_event_create_with_email_invitations
```

### Email Configuration
Development (current):
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Production:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## For Users (Event Organizers)

### Creating an Event

1. **Navigate**: Dashboard → Create Event

2. **Fill Required Fields** (marked with *):
   - Title
   - Description
   - Event Type
   - Start Date & Time

3. **Optional: Send Invitations**
   - Scroll to "Invite via Email" field
   - Enter email addresses (comma or newline separated)
   - Example:
     ```
     john@example.com, jane@example.com
     bob@company.com
     ```

4. **Submit**: Click "Create Event"

5. **Result**:
   - Event created with 'draft' status
   - Invitations sent (if emails provided)
   - Success message shows count

### Email Invitation Format

Recipients receive:
- Event title and description
- Date, time, and location
- Direct registration link
- Your contact information

### Publishing Your Event

After creation, your event is in 'draft' status. To publish:
1. Go to event detail page
2. Click "Edit Event"
3. Change status to "Published"
4. Save changes

## For QA/Testing

### Test Scenarios

#### Scenario 1: Create Event Without Invitations
```
1. Login as organizer
2. Navigate to Create Event
3. Fill required fields
4. Leave "Invite via Email" empty
5. Submit
Expected: Event created with draft status, no emails sent
```

#### Scenario 2: Create Event With Valid Emails
```
1. Login as organizer
2. Navigate to Create Event
3. Fill required fields
4. Add emails: "test1@example.com, test2@example.com"
5. Submit
Expected: Event created, 2 invitations sent, success message shows count
```

#### Scenario 3: Create Event With Invalid Email
```
1. Login as organizer
2. Navigate to Create Event
3. Fill required fields
4. Add invalid email: "not-an-email"
5. Submit
Expected: Form validation error, event not created
```

#### Scenario 4: Verify Status Auto-Assignment
```
1. Create event (any method)
2. Check event detail page
Expected: Status shows "Draft"
```

#### Scenario 5: API Event Creation
```
POST /api/v1/events/
{
  "title": "API Test Event",
  "description": "Test",
  "event_type": "virtual",
  "start_date": "2026-12-01T10:00:00Z",
  "end_date": "2026-12-01T18:00:00Z"
}
Expected: 201 Created, response includes "status": "draft"
```

### Validation Rules

**Email Field**:
- ✅ Valid: "user@domain.com"
- ✅ Valid: "user1@domain.com, user2@domain.com"
- ✅ Valid: Multiple lines
- ✅ Valid: Empty (optional field)
- ❌ Invalid: "not-an-email"
- ❌ Invalid: "user@" (incomplete)

**Status Field**:
- Not visible in form
- Always set to 'draft' on creation
- Can be changed after creation via edit

## Troubleshooting

### Emails Not Sending

**Check 1**: Email backend configuration
```bash
# In Django shell
python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_BACKEND)
```

**Check 2**: Console output (development mode)
- Emails should appear in console/terminal
- Look for "Subject: You're Invited:"

**Check 3**: SMTP credentials (production)
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Check firewall/security settings
- Enable "Less secure app access" (Gmail) or use app passwords

### Form Validation Errors

**Issue**: "Invalid email address"
- Check for typos in email addresses
- Ensure proper format: user@domain.com
- Remove extra spaces

**Issue**: "This field is required"
- Fill all fields marked with * (asterisk)
- Title, Description, Event Type, Start Date are required

### Status Not Showing as Draft

**Check**: Database
```bash
python manage.py shell
>>> from events.models import Event
>>> event = Event.objects.latest('created_at')
>>> print(event.status)
# Should print: draft
```

## Support

For issues or questions:
1. Check this guide first
2. Review CHANGES.md for detailed implementation
3. Check IMPLEMENTATION_SUMMARY.md for technical details
4. Review test cases in events/tests.py

## Rollback (If Needed)

To revert changes:
```bash
git revert <commit-hash>
```

Or manually:
1. Add 'status' back to EventForm.Meta.fields
2. Remove invite_emails field from EventForm
3. Remove send_event_invitations() function
4. Revert event_create view changes
