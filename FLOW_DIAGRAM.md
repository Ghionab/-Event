# Event Creation Flow Diagram

## Complete Flow with New Features

```
┌─────────────────────────────────────────────────────────────────┐
│                     EVENT CREATION FLOW                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐
│   User      │
│  (Organizer)│
└──────┬──────┘
       │
       │ 1. Navigate to Create Event
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVENT CREATION FORM                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Title *                    [________________]            │  │
│  │ Description *              [________________]            │  │
│  │ Event Type *               [In-Person ▼]                 │  │
│  │ ❌ Status (REMOVED)                                      │  │
│  │ Start Date & Time *        [2026-03-15 09:00]           │  │
│  │ End Date & Time            [2026-03-15 17:00]           │  │
│  │ Venue Name                 [________________]            │  │
│  │ City                       [________________]            │  │
│  │ Country                    [________________]            │  │
│  │ ...                                                       │  │
│  │                                                           │  │
│  │ ✨ NEW: Invite via Email                                 │  │
│  │ ┌───────────────────────────────────────────────────┐   │  │
│  │ │ user1@example.com, user2@example.com             │   │  │
│  │ │ user3@example.com                                 │   │  │
│  │ └───────────────────────────────────────────────────┘   │  │
│  │ Optional: Send event invitations to these emails         │  │
│  │                                                           │  │
│  │              [Cancel]  [Create Event]                    │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
       │
       │ 2. User submits form
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FORM VALIDATION                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ • Validate required fields                               │ │
│  │ • Validate email addresses (if provided)                 │ │
│  │ • Check date logic                                       │ │
│  │ • Validate file uploads                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
       │
       │ Valid?
       ├─── No ──────────────────┐
       │                          │
       │ Yes                      ▼
       ▼                   ┌─────────────┐
┌─────────────────────┐   │   Show      │
│  CREATE EVENT       │   │  Validation │
│                     │   │   Errors    │
│  event.status =     │   └─────────────┘
│    'draft' ✨       │          │
│  (Auto-assigned)    │          │
│                     │          │
│  event.organizer =  │          │
│    current_user     │          │
│                     │          │
│  event.save()       │          │
└──────┬──────────────┘          │
       │                          │
       │ 3. Event created         │
       ▼                          │
┌─────────────────────────────────┴───────────────────────────────┐
│              EMAIL INVITATION LOGIC                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ invite_emails = form.cleaned_data.get('invite_emails')   │ │
│  │                                                           │ │
│  │ if invite_emails:                                         │ │
│  │     for email in invite_emails:                           │ │
│  │         send_invitation(event, email, organizer)          │ │
│  │     show_success_with_count()                             │ │
│  │ else:                                                      │ │
│  │     show_success()                                        │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
       │
       │ 4. Send emails (if provided)
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EMAIL SENDING                                │
│                                                                 │
│  For each email address:                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Subject: You're Invited: [Event Title]                   │ │
│  │                                                           │ │
│  │ Dear Guest,                                               │ │
│  │                                                           │ │
│  │ You have been invited to attend [Event Title]!           │ │
│  │                                                           │ │
│  │ Event Details:                                            │ │
│  │ - Event: [Event Title]                                    │ │
│  │ - Date: [Date and Time]                                   │ │
│  │ - Venue: [Venue Name]                                     │ │
│  │ - Location: [City, Country]                               │ │
│  │                                                           │ │
│  │ [Description Preview]                                     │ │
│  │                                                           │ │
│  │ Register now: http://domain.com/events/[ID]/             │ │
│  │                                                           │ │
│  │ Best regards,                                             │ │
│  │ [Organizer Name]                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
       │
       │ 5. Show success message
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUCCESS FEEDBACK                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ✓ Event created! Sent 3 invitation(s).                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  OR (if no emails)                                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ✓ Event created successfully!                            │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
       │
       │ 6. Redirect to event detail
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVENT DETAIL PAGE                            │
│                                                                 │
│  Event: Demo Tech Conference 2026                               │
│  Status: 📝 Draft  ✨ (Auto-assigned)                          │
│  Date: March 15, 2026                                           │
│  Venue: Convention Center                                       │
│  Location: San Francisco, USA                                   │
│                                                                 │
│  [Edit Event] [Publish] [Delete]                                │
└─────────────────────────────────────────────────────────────────┘
```

## API Flow

```
┌─────────────┐
│  API Client │
└──────┬──────┘
       │
       │ POST /api/v1/events/
       │ {
       │   "title": "API Event",
       │   "description": "...",
       │   "event_type": "virtual",
       │   "start_date": "2026-03-15T09:00:00Z",
       │   "end_date": "2026-03-15T17:00:00Z"
       │   // ❌ No status field needed
       │ }
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API ENDPOINT                                 │
│                                                                 │
│  EventCreateSerializer.create():                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ validated_data['organizer'] = request.user               │ │
│  │ validated_data['status'] = 'draft'  ✨ Auto-assign       │ │
│  │ return super().create(validated_data)                    │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
       │
       │ 201 Created
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API RESPONSE                                 │
│                                                                 │
│  {                                                              │
│    "id": 123,                                                   │
│    "title": "API Event",                                        │
│    "status": "draft",  ✨ Auto-assigned                        │
│    "event_type": "virtual",                                     │
│    "start_date": "2026-03-15T09:00:00Z",                        │
│    "end_date": "2026-03-15T17:00:00Z",                          │
│    ...                                                          │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Email Validation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                EMAIL VALIDATION PROCESS                         │
└─────────────────────────────────────────────────────────────────┘

Input: "user1@example.com, user2@example.com\nuser3@example.com"
       │
       │ 1. Split by comma or newline
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  ['user1@example.com', 'user2@example.com', 'user3@example.com']│
└─────────────────────────────────────────────────────────────────┘
       │
       │ 2. For each email
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATE EMAIL                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ email = email.strip()                                     │ │
│  │ validate_email(email)  # Django validator                │ │
│  │                                                           │ │
│  │ Valid? ──Yes──> Add to cleaned_emails                    │ │
│  │   │                                                       │ │
│  │   No                                                      │ │
│  │   │                                                       │ │
│  │   └──> Raise ValidationError                             │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
       │
       │ 3. Return cleaned emails
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  ['user1@example.com', 'user2@example.com', 'user3@example.com']│
└─────────────────────────────────────────────────────────────────┘
```

## Status Assignment Comparison

### BEFORE (Manual)
```
┌──────────────┐
│ User selects │
│   status     │
│   ▼          │
│ [Draft    ▼] │ ← User could select any status
│ [Published  ]│
│ [Ongoing    ]│
│ [Completed  ]│
│ [Cancelled  ]│
└──────────────┘
       │
       ▼
┌──────────────┐
│ Event saved  │
│ with selected│
│   status     │
└──────────────┘

Risk: User could accidentally publish draft event!
```

### AFTER (Automatic)
```
┌──────────────┐
│ Status field │
│   REMOVED    │
│   from form  │
└──────────────┘
       │
       ▼
┌──────────────┐
│ System auto- │
│  assigns     │
│ status='draft'│
└──────────────┘
       │
       ▼
┌──────────────┐
│ Event saved  │
│ with 'draft' │
│   status     │
└──────────────┘

Safe: Always starts as draft, must be explicitly published later
```

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Event Creation Form                          │ │
│  │  • No status field                                        │ │
│  │  • New invite_emails field                                │ │
│  │  • Form validation                                        │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND                                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                  events/forms.py                          │ │
│  │  • EventForm (status removed, invite_emails added)        │ │
│  │  • clean_invite_emails() validation                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                  events/views.py                          │ │
│  │  • event_create() - Auto-assign status                    │ │
│  │  • send_event_invitations() - Send emails                │ │
│  └──────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                  events/models.py                         │ │
│  │  • Event model (unchanged)                                │ │
│  │  • status field with choices                              │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATABASE                                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                  events_event                             │ │
│  │  • id                                                     │ │
│  │  • title                                                  │ │
│  │  • status = 'draft' ✨ (auto-assigned)                   │ │
│  │  • organizer_id                                           │ │
│  │  • ...                                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EMAIL SYSTEM                                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Django Email Backend                                     │ │
│  │  • Console (development)                                  │ │
│  │  • SMTP (production)                                      │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Legend

```
✨ = New feature
❌ = Removed feature
✓ = Success
⚠ = Warning
📝 = Draft status
```

---

**This diagram shows the complete flow of the enhanced event creation system.**
