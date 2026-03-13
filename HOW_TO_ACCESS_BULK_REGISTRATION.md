# How to Access Mass/Bulk Registration

## Quick Answer
Mass registration (bulk upload) is located in the **Registrations** section and can be accessed through **3 different paths**.

---

## Access Path 1: From Event Detail Page ⭐ (Easiest)

### Steps:
1. Login to Organizer Portal
2. Go to **My Events** (sidebar)
3. Click on any event
4. Click the **"Manage Registrations"** button (purple button)
5. You'll see the Manual Registration List page
6. Click **"Bulk Upload"** button (purple button at top)

### Visual Path:
```
Dashboard → My Events → [Select Event] → Manage Registrations → Bulk Upload
```

### Screenshot Guide:
```
┌─────────────────────────────────────┐
│ Event Detail Page                   │
├─────────────────────────────────────┤
│ [Edit Event] [Manage Registrations] │  ← Click this purple button
│              [Analytics] [Back]     │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Manual Registrations                │
├─────────────────────────────────────┤
│ [Add Attendee] [Bulk Upload] [Back] │  ← Click this purple button
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Bulk Registration Upload            │
│ Upload attendee list from CSV/Excel │
└─────────────────────────────────────┘
```

---

## Access Path 2: From Registrations Sidebar Tab

### Steps:
1. Login to Organizer Portal
2. Click **"Registrations"** in the sidebar (under Management section)
3. Filter by event OR select an event from the dropdown
4. Click **"Bulk Upload"** button (purple button at top)

### Visual Path:
```
Dashboard → Registrations (sidebar) → [Filter by Event] → Bulk Upload
```

### Screenshot Guide:
```
Sidebar:
┌──────────────────┐
│ Dashboard        │
│ My Events        │
│ Create Event     │
├──────────────────┤
│ Management       │
│ → Registrations  │  ← Click here
│   Communication  │
│   Sponsors       │
└──────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│ All Registrations                           │
├─────────────────────────────────────────────┤
│ Event: [Select Event ▼]                     │
│ [Add Attendee] [Bulk Upload] [Export CSV]   │  ← Click Bulk Upload
└─────────────────────────────────────────────┘
```

**Note:** The "Bulk Upload" button only appears when you have selected a specific event.

---

## Access Path 3: Direct URL (Advanced)

If you know the event ID, you can access it directly:

```
/registration/bulk/upload/<event_id>/
```

Example:
```
http://localhost:8000/registration/bulk/upload/1/
```

---

## What You'll See on the Bulk Upload Page

### Features:
1. **File Upload Section**
   - Choose file type (Excel or CSV)
   - Drag & drop or click to upload
   - Options:
     - ☑ First row contains headers
     - ☑ Send invitation emails

2. **File Format Instructions**
   - Required fields: name, email
   - Optional fields: phone, company, job_title
   - Download CSV template button

3. **Upload History**
   - Table showing all previous uploads
   - Status: completed, failed, processing
   - Success/error counts
   - View details link

### Example CSV Format:
```csv
name,email,phone,company,job_title
John Doe,john@example.com,+1234567890,Acme Inc,Developer
Jane Smith,jane@example.com,+0987654321,Tech Corp,Manager
```

---

## Complete Navigation Map

```
Organizer Portal
│
├── My Events
│   └── Event Detail
│       └── [Manage Registrations] ← Path 1
│           ├── Manual Registration List
│           │   └── [Bulk Upload] ← Bulk Registration Page
│           └── [Add Attendee] ← Single attendee
│
└── Registrations (Sidebar)
    └── Registration List
        └── [Filter by Event]
            └── [Bulk Upload] ← Path 2 (Bulk Registration Page)
```

---

## URLs Reference

### Main URLs:
- **Manual Registration List**: `/registration/manual/list/<event_id>/`
- **Bulk Upload**: `/registration/bulk/upload/<event_id>/`
- **Add Single Attendee**: `/registration/manual/create/<event_id>/`

### URL Names (for templates):
```python
registration:manual_registration_list      # Manual registration list
registration:bulk_registration_upload      # Bulk upload page
registration:manual_registration_create    # Add single attendee
registration:bulk_registration_detail      # View upload details
```

---

## Quick Test

To verify bulk registration is working:

1. **Go to Event Detail**
   ```
   Dashboard → My Events → Click any event
   ```

2. **Click "Manage Registrations"** (purple button)

3. **You should see:**
   - Manual Registration List page
   - Two buttons at top: "Add Attendee" and "Bulk Upload"

4. **Click "Bulk Upload"**

5. **You should see:**
   - Bulk Registration Upload page
   - File upload interface
   - CSV template download link
   - Upload history table

---

## Troubleshooting

### "Bulk Upload button not showing"
**Solution:** Make sure you're viewing registrations for a specific event, not all registrations.

### "404 Error when clicking Bulk Upload"
**Solution:** Check that the URL includes the event ID: `/registration/bulk/upload/<event_id>/`

### "Permission denied"
**Solution:** Make sure you're logged in as an organizer and have access to the event.

---

## Files Location

### Templates:
- `registration/templates/registration/bulk_upload.html` - Main bulk upload page
- `registration/templates/registration/manual_registration_list.html` - List with bulk upload button
- `organizers/templates/organizers/event_detail.html` - Event detail with Manage Registrations button

### Views:
- `registration/views.py` - Contains `bulk_registration_upload()` view

### URLs:
- `registration/urls.py` - Contains bulk registration routes

---

## Summary

**Easiest Way to Access:**
1. Go to **My Events**
2. Click on an event
3. Click **"Manage Registrations"** (purple button)
4. Click **"Bulk Upload"** (purple button)

**Alternative Way:**
1. Click **"Registrations"** in sidebar
2. Select an event from filter
3. Click **"Bulk Upload"** (purple button)

Both paths lead to the same bulk registration upload page where you can upload CSV/Excel files with multiple attendees.

---

**Last Updated:** March 12, 2026
