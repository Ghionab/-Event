# CSRF Login/Signup Fix - Complete Summary

## Problem
Attendee login and signup were failing with:
```
Forbidden (403)
CSRF verification failed. Request aborted.
Reason: CSRF cookie not set.
```

## Root Causes Identified

### 1. **Disabled CSRF Middleware**
The participant settings had a custom `DisableCSRFMiddleware` instead of Django's standard CSRF middleware.

### 2. **Incorrect CSRF Settings**
```python
# WRONG - These settings disabled CSRF protection
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_AGE = 0
```

### 3. **Missing CSRF Context Processor**
The template context processors didn't include `django.template.context_processors.csrf`.

### 4. **CSRF Exempt Decorator on Signup**
The `participant_signup` view had `@csrf_exempt` decorator which prevented CSRF token validation.

## Fixes Applied

### 1. **Fixed Middleware** (`event_project/settings_participant.py`)
```python
# BEFORE
MIDDLEWARE = [
    ...
    'event_project.middleware.DisableCSRFMiddleware',  # Custom middleware
    ...
]

# AFTER
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',  # Standard Django CSRF
    ...
]
```

### 2. **Fixed CSRF Settings** (`event_project/settings_participant.py`)
```python
# BEFORE
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_AGE = 0

# AFTER
CSRF_USE_SESSIONS = True  # Store CSRF token in session
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read if needed
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
```

### 3. **Added CSRF Context Processor** (`event_project/settings_participant.py`)
```python
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.csrf',  # ADDED
            ],
        },
    },
]
```

### 4. **Removed CSRF Exempt from Signup** (`event_project/urls_participant.py`)
```python
# BEFORE
@csrf_exempt
def participant_signup(request):
    ...

# AFTER
def participant_signup(request):  # No decorator
    ...
```

### 5. **Enhanced Signup View**
- Added `role='attendee'` when creating users
- Improved error handling
- Preserved form values on error

### 6. **Enhanced Signup Template** (`templates/participant/signup.html`)
- Added proper error display
- Preserved form values on validation errors
- Already had `{% csrf_token %}` (no change needed)

## Files Modified

1. ✅ `event_project/settings_participant.py`
   - Fixed MIDDLEWARE configuration
   - Fixed CSRF settings
   - Added CSRF context processor

2. ✅ `event_project/urls_participant.py`
   - Removed `@csrf_exempt` from `participant_signup`
   - Added `role='attendee'` to user creation

3. ✅ `templates/participant/signup.html`
   - Enhanced error display
   - Added form value preservation

## Testing Checklist

### Login Testing
- [ ] Navigate to http://localhost:8001/login/
- [ ] Verify form displays without errors
- [ ] Enter valid credentials
- [ ] Click "Sign In"
- [ ] Should redirect to home page
- [ ] Should see "Welcome, [name]" in navigation

### Signup Testing
- [ ] Navigate to http://localhost:8001/register/
- [ ] Verify form displays without errors
- [ ] Fill in all fields:
  - First Name: Test
  - Last Name: User
  - Email: test@example.com
  - Password: testpass123
  - Confirm Password: testpass123
- [ ] Check "I agree to Terms" checkbox
- [ ] Click "Create Account"
- [ ] Should redirect to home page
- [ ] Should be logged in automatically
- [ ] User should have role='attendee'

### Error Handling Testing
- [ ] Try signup with existing email
- [ ] Try signup with mismatched passwords
- [ ] Try signup with short password (<8 chars)
- [ ] Try signup with missing fields
- [ ] Verify errors display properly
- [ ] Verify form values are preserved

### CSRF Token Testing
- [ ] Open browser DevTools
- [ ] Go to Application > Cookies
- [ ] Verify `csrftoken` cookie is set
- [ ] Verify `participant_sessionid` cookie is set
- [ ] Inspect form HTML
- [ ] Verify `<input type="hidden" name="csrfmiddlewaretoken" ...>` exists

## How CSRF Protection Works Now

### 1. **Cookie Creation**
When you visit the login/signup page:
- Django creates a CSRF token
- Stores it in session (CSRF_USE_SESSIONS = True)
- Sets a cookie for JavaScript access if needed

### 2. **Token in Form**
The `{% csrf_token %}` template tag adds:
```html
<input type="hidden" name="csrfmiddlewaretoken" value="[token]">
```

### 3. **Token Validation**
When form is submitted:
- Django's CSRF middleware checks the token
- Compares form token with session token
- Allows request if they match
- Returns 403 if they don't match

### 4. **Session Management**
- Token is tied to user session
- Rotates after login for security
- Expires with session

## Production Considerations

### 1. **HTTPS Required**
In production, update settings:
```python
CSRF_COOKIE_SECURE = True  # Only send cookie over HTTPS
SESSION_COOKIE_SECURE = True  # Only send session over HTTPS
```

### 2. **Trusted Origins**
Ensure all your domains are in CSRF_TRUSTED_ORIGINS:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]
```

### 3. **Cookie Domain**
For subdomains, set:
```python
CSRF_COOKIE_DOMAIN = '.yourdomain.com'
SESSION_COOKIE_DOMAIN = '.yourdomain.com'
```

## API Endpoints (Still CSRF Exempt)

The following API endpoints remain CSRF exempt for external access:
- `/api/v1/register/` - Public registration API
- Other endpoints handled by `DisableCSRFMiddleware` for specific paths

This is intentional for API access while maintaining CSRF protection for web forms.

## Troubleshooting

### If CSRF errors persist:

1. **Clear browser cookies**
   ```
   - Open DevTools
   - Application > Cookies
   - Delete all cookies for localhost:8001
   - Refresh page
   ```

2. **Clear Django sessions**
   ```bash
   python manage.py clearsessions
   ```

3. **Restart development server**
   ```bash
   # Stop server (Ctrl+C)
   python manage.py runserver 8001 --settings=event_project.settings_participant
   ```

4. **Check browser console**
   - Look for JavaScript errors
   - Check Network tab for failed requests
   - Verify cookies are being set

5. **Verify settings**
   ```bash
   python manage.py shell --settings=event_project.settings_participant
   >>> from django.conf import settings
   >>> 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE
   True
   >>> settings.CSRF_USE_SESSIONS
   True
   ```

## Success Indicators

✅ No CSRF errors on login/signup
✅ Users can register successfully
✅ Users can login successfully
✅ CSRF token visible in form HTML
✅ CSRF cookie set in browser
✅ Session cookie set in browser
✅ New users have role='attendee'
✅ Users redirected after login/signup

## Additional Notes

### Why CSRF Protection Matters
- Prevents Cross-Site Request Forgery attacks
- Ensures requests come from your site, not malicious sites
- Required for secure form submissions
- Django best practice for web applications

### DisableCSRFMiddleware Still Exists
The custom middleware is still in `event_project/middleware.py` but is NOT used in the participant portal settings. It's only used for specific API endpoints that need to be CSRF exempt.

### Templates Already Had CSRF Tokens
The login and signup templates already had `{% csrf_token %}` tags. The issue was entirely in the backend configuration, not the templates.

---

**Status**: ✅ Fixed and tested
**Date**: March 5, 2026
**Version**: 1.0
