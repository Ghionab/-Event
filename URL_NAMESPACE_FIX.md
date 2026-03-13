# URL Namespace Fix

## Issue
`NoReverseMatch` error: `'organizers' is not a registered namespace`

### Error Details:
```
NoReverseMatch at /registration/manual/list/4/
'organizers' is not a registered namespace

Exception Location: django/urls/base.py, line 92, in reverse
Raised during: registration.views.manual_registration_list
```

## Root Cause
The organizers app does not use a URL namespace. The URLs are registered directly without `app_name`, so they should be referenced without a namespace prefix.

### Incorrect Usage:
```python
{% url 'organizers:event_detail' event.id %}  # ❌ Wrong - namespace doesn't exist
```

### Correct Usage:
```python
{% url 'organizer_event_detail' event.id %}  # ✅ Correct - no namespace
```

## Files Fixed

### 1. `registration/templates/registration/manual_registration_list.html`
**Line 23:**
- **Before:** `{% url 'organizers:event_detail' event.id %}`
- **After:** `{% url 'organizer_event_detail' event.id %}`

### 2. `registration/templates/registration/bulk_upload.html`
**Line 20:**
- **Before:** `{% url 'organizers:event_detail' event.id %}`
- **After:** `{% url 'organizer_event_detail' event.id %}`

### 3. `registration/templates/registration/qr_code_list.html`
**Line 19:**
- **Before:** `{% url 'organizers:event_detail' event.id %}`
- **After:** `{% url 'organizer_event_detail' event.id %}`

## Organizer URL Names Reference

The organizers app URLs are registered without a namespace. Here are the correct URL names:

```python
# From organizers/urls.py
organizer_login                      # /organizers/login/
organizer_logout                     # /organizers/logout/
organizer_create                     # /organizers/create/
organizer_dashboard                  # /organizers/dashboard/
organizer_event_list                 # /organizers/events/
organizer_event_create               # /organizers/events/create/
organizer_event_setup                # /organizers/events/<id>/setup/
organizer_event_detail               # /organizers/events/<id>/
organizer_event_edit                 # /organizers/events/<id>/edit/
organizer_event_delete               # /organizers/events/<id>/delete/
organizer_registration_list          # /organizers/registrations/
organizer_registration_export        # /organizers/registrations/export/
# ... and more
```

## How to Use Organizer URLs

### In Templates:
```django
<!-- Correct ✅ -->
<a href="{% url 'organizer_event_detail' event.id %}">Event Detail</a>
<a href="{% url 'organizer_dashboard' %}">Dashboard</a>
<a href="{% url 'organizer_event_list' %}">My Events</a>

<!-- Incorrect ❌ -->
<a href="{% url 'organizers:event_detail' event.id %}">Event Detail</a>
<a href="{% url 'organizers:dashboard' %}">Dashboard</a>
```

### In Views:
```python
# Correct ✅
from django.shortcuts import redirect
return redirect('organizer_event_detail', event_id=event.id)
return redirect('organizer_dashboard')

# Incorrect ❌
return redirect('organizers:event_detail', event_id=event.id)
```

## Apps with Namespaces

For reference, these apps DO use namespaces:

### Registration App:
```python
# registration/urls.py
app_name = 'registration'

# Usage:
{% url 'registration:manual_registration_list' event.id %}
{% url 'registration:bulk_registration_upload' event.id %}
```

### Advanced App:
```python
# advanced/urls.py
app_name = 'advanced'

# Usage:
{% url 'advanced:team_list' %}
{% url 'advanced:team_member_create' %}
```

### Business App:
```python
# business/urls.py
app_name = 'business'

# Usage:
{% url 'business:report_list' %}
```

## Testing

After this fix, the following should work without errors:

1. Navigate to Event Detail page
2. Click "Manage Registrations"
3. Manual Registration List page should load successfully
4. Click "Back to Event" - should return to Event Detail
5. Click "Bulk Upload" - should load bulk upload page
6. Click "Back to Event" - should return to Event Detail

## Status: ✅ Fixed

All instances of incorrect namespace usage have been corrected.

**Date:** March 12, 2026
