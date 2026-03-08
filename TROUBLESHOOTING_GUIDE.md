# Troubleshooting Guide

## Issue 1: Status Field Still Showing

The status field has been successfully removed from the code. If you're still seeing it:

### Solution:
1. **Clear browser cache**: Press `Ctrl + Shift + Delete` (or `Cmd + Shift + Delete` on Mac)
2. **Hard refresh**: Press `Ctrl + F5` (or `Cmd + Shift + R` on Mac)
3. **Clear Django cache**: Run `python manage.py clear_cache` (if available)
4. **Restart server**: Stop and restart the development server

### Verification:
Run this command to verify the form is correct:
```bash
python manage.py shell -c "from events.forms import EventForm; f = EventForm(); print('Status in fields:', 'status' in f.fields)"
```

Expected output: `Status in fields: False`

---

## Issue 2: Reports Tab Not Working

The reports functionality exists in the `business` app.

### Check URL Configuration:
1. Navigate to: `http://localhost:8000/business/reports/`
2. Or from dashboard: Business → Reports

### If you get a 404 error:
Check if the URL is included in the main urls.py:
```python
path('business/', include('business.urls')),
```

### If you get a permission error:
Make sure your user has the correct role:
- User must be `staff` or `organizer`
- Check in Django admin or database

---

## Issue 3: Tasks Tab Showing Nothing

The tasks tab was missing data in the template context.

### Fixed:
Updated `advanced/views.py` to pass `statuses` and `priorities` to the template.

### Verification:
1. Navigate to: `http://localhost:8000/advanced/tasks/`
2. You should see the task list with filters

### If still empty:
1. **Create a test task**:
   - Click "Create Task" button
   - Fill in the form
   - Submit

2. **Check permissions**:
   - User must have `advanced.view_task` permission
   - Check in Django admin → Users → Permissions

3. **Check database**:
   ```bash
   python manage.py shell -c "from advanced.models import Task; print('Total tasks:', Task.objects.count())"
   ```

---

## General Troubleshooting Steps

### 1. Restart Development Server
```bash
# Stop the server (Ctrl+C)
# Then restart:
python manage.py runserver
```

### 2. Clear Python Cache
```bash
# Windows
del /s *.pyc
del /s __pycache__

# Linux/Mac
find . -type f -name '*.pyc' -delete
find . -type d -name '__pycache__' -delete
```

### 3. Check for Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Check Server Logs
Look at the terminal where the server is running for any error messages.

### 5. Check Browser Console
Press F12 in your browser and check the Console tab for JavaScript errors.

---

## Quick Fixes

### Clear Everything and Start Fresh:
```bash
# Stop server
# Clear cache
find . -type f -name '*.pyc' -delete
find . -type d -name '__pycache__' -delete

# Restart server
python manage.py runserver
```

### Force Browser to Reload:
1. Open the page
2. Press `Ctrl + Shift + R` (hard reload)
3. Or open in incognito/private mode

---

## Verification Commands

### Check Event Form:
```bash
python manage.py shell -c "from events.forms import EventForm; f = EventForm(); print('Fields:', list(f.fields.keys()))"
```

### Check Tasks:
```bash
python manage.py shell -c "from advanced.models import Task; print('Tasks:', Task.objects.count())"
```

### Check Reports:
```bash
python manage.py shell -c "from business.models import Report; print('Reports:', Report.objects.count())"
```

---

## Still Having Issues?

1. Check the server is running: `http://localhost:8000/`
2. Check you're logged in as an organizer or admin
3. Check the URL you're accessing is correct
4. Check browser console for errors (F12)
5. Check server terminal for errors

---

## Contact Information

If issues persist after trying all troubleshooting steps:
1. Check the implementation files
2. Review the CHANGES.md document
3. Run the demo scripts to verify functionality
