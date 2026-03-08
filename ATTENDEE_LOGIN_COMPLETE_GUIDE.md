# Complete Attendee Login/Signup Guide

## Quick Start

### 1. Start the Participant Portal
```bash
python manage.py runserver 8001 --settings=event_project.settings_participant
```

### 2. Access the Portal
- Home: http://localhost:8001/
- Login: http://localhost:8001/login/
- Signup: http://localhost:8001/register/

### 3. Test the Fix
```bash
python test_csrf_fix.py
```

## What Was Fixed

### Problem
Login and signup forms were returning:
```
Forbidden (403)
CSRF verification failed. Request aborted.
```

### Solution
Fixed 4 critical issues in the participant portal configuration:

1. ✅ Enabled proper CSRF middleware
2. ✅ Configured CSRF settings correctly
3. ✅ Added CSRF context processor
4. ✅ Removed CSRF exempt decorator from signup

## Files Modified

### 1. `event_project/settings_participant.py`
**Changes:**
- Replaced custom `DisableCSRFMiddleware` with Django's `CsrfViewMiddleware`
- Fixed CSRF settings (CSRF_USE_SESSIONS, CSRF_COOKIE_SAMESITE, etc.)
- Added `django.template.context_processors.csrf` to context processors

### 2. `event_project/urls_participant.py`
**Changes:**
- Removed `@csrf_exempt` decorator from `participant_signup` view
- Added `role='attendee'` when creating new users
- Enhanced error handling

### 3. `templates/participant/signup.html`
**Changes:**
- Enhanced error display with list format
- Added form value preservation on errors
- (CSRF token was already present)

## Testing Instructions

### Manual Testing

#### Test Signup
1. Go to http://localhost:8001/register/
2. Fill in the form:
   - First Name: John
   - Last Name: Doe
   - Email: john.doe@example.com
   - Password: password123
   - Confirm Password: password123
3. Check "I agree to Terms"
4. Click "Create Account"
5. ✅ Should redirect to home page
6. ✅ Should be logged in
7. ✅ Should see "Welcome, John" in navigation

#### Test Login
1. Go to http://localhost:8001/login/
2. Enter credentials:
   - Email: john.doe@example.com
   - Password: password123
3. Click "Sign In"
4. ✅ Should redirect to home page
5. ✅ Should be logged in

#### Test Error Handling
1. Try signup with existing email
   - ✅ Should show error: "An account with this email already exists"
2. Try signup with mismatched passwords
   - ✅ Should show error: "Passwords do not match"
3. Try signup with short password
   - ✅ Should show error: "Password must be at least 8 characters"
4. ✅ Form values should be preserved

### Automated Testing
```bash
python test_csrf_fix.py
```

Expected output:
```
============================================================
CSRF FIX VERIFICATION SCRIPT
============================================================

============================================================
TESTING CSRF CONFIGURATION
============================================================

1. Checking CSRF Middleware...
   ✅ django.middleware.csrf.CsrfViewMiddleware is enabled

2. Checking CSRF Settings...
   CSRF_USE_SESSIONS: True
   CSRF_COOKIE_HTTPONLY: False
   CSRF_COOKIE_SAMESITE: Lax

3. Checking Context Processors...
   ✅ django.template.context_processors.csrf is enabled

============================================================
TESTING SIGNUP VIEW
============================================================

1. Testing GET request to /register/...
   ✅ GET request successful (status: 200)
   ✅ CSRF token found in form

2. Testing POST request with CSRF token...
   ✅ POST request successful (status: 200)
   ✅ User created successfully
   ✅ User role: attendee
   ✅ Test user cleaned up

============================================================
TESTING LOGIN VIEW
============================================================

1. Testing GET request to /login/...
   ✅ GET request successful (status: 200)
   ✅ CSRF token found in form

============================================================
TEST SUMMARY
============================================================
CSRF Configuration: ✅ PASSED
Signup View: ✅ PASSED
Login View: ✅ PASSED

============================================================
✅ ALL TESTS PASSED - CSRF FIX VERIFIED!
============================================================
```

## Verification Checklist

### Browser DevTools Verification
1. Open http://localhost:8001/login/
2. Open DevTools (F12)
3. Go to Application > Cookies
4. ✅ Verify `csrftoken` cookie exists
5. ✅ Verify `participant_sessionid` cookie exists
6. Go to Elements tab
7. Inspect the form
8. ✅ Verify `<input type="hidden" name="csrfmiddlewaretoken" ...>` exists

### Database Verification
```bash
python manage.py shell --settings=event_project.settings_participant
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Check if test user was created
user = User.objects.filter(email='john.doe@example.com').first()
if user:
    print(f"User: {user.email}")
    print(f"Role: {user.role}")  # Should be 'attendee'
    print(f"Name: {user.first_name} {user.last_name}")
```

## How It Works Now

### 1. User Visits Login/Signup Page
```
Browser → GET /login/ → Django
                      ↓
                CSRF Middleware creates token
                      ↓
                Stores in session
                      ↓
                Sets cookie (if needed)
                      ↓
                Template renders with {% csrf_token %}
                      ↓
                Browser ← HTML with hidden CSRF input
```

### 2. User Submits Form
```
Browser → POST /login/ (with CSRF token) → Django
                                          ↓
                                    CSRF Middleware
                                          ↓
                                    Validates token
                                          ↓
                                    ✅ Token matches
                                          ↓
                                    Process login
                                          ↓
                                    Redirect to home
                                          ↓
                        Browser ← Redirect response
```

### 3. CSRF Token Lifecycle
```
1. Token Created: When session starts
2. Token Stored: In session (CSRF_USE_SESSIONS=True)
3. Token Sent: In form as hidden input
4. Token Validated: On POST request
5. Token Rotated: After successful login (security)
```

## Configuration Details

### CSRF Settings (settings_participant.py)
```python
# Enable CSRF protection
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',  # Required
    ...
]

# CSRF configuration
CSRF_USE_SESSIONS = True  # Store token in session
CSRF_COOKIE_HTTPONLY = False  # Allow JS access if needed
CSRF_COOKIE_SAMESITE = 'Lax'  # Prevent CSRF attacks
CSRF_COOKIE_SECURE = False  # Set True in production (HTTPS)

# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8001',
    'http://localhost:8001',
]

# Context processors (required for {% csrf_token %})
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'django.template.context_processors.csrf',  # Required
                ...
            ],
        },
    },
]
```

## Troubleshooting

### Issue: Still getting CSRF errors

**Solution 1: Clear browser data**
```
1. Open DevTools (F12)
2. Application > Storage > Clear site data
3. Refresh page
```

**Solution 2: Restart server**
```bash
# Stop server (Ctrl+C)
python manage.py runserver 8001 --settings=event_project.settings_participant
```

**Solution 3: Clear Django sessions**
```bash
python manage.py clearsessions --settings=event_project.settings_participant
```

### Issue: CSRF token not in form

**Check template:**
```html
<form method="post">
    {% csrf_token %}  <!-- Must be inside form -->
    ...
</form>
```

**Check context processor:**
```python
# In settings_participant.py
'django.template.context_processors.csrf'  # Must be in context_processors
```

### Issue: User created but not logged in

**Check authentication backend:**
```python
# In settings.py
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
```

**Check user creation:**
```python
# In participant_signup view
user = User.objects.create_user(
    email=email,
    password=password1,  # Must use create_user, not create
    ...
)
```

## Production Deployment

### Required Changes for Production

1. **Enable HTTPS**
```python
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
```

2. **Set Proper Domain**
```python
CSRF_COOKIE_DOMAIN = '.yourdomain.com'
SESSION_COOKIE_DOMAIN = '.yourdomain.com'
```

3. **Update Trusted Origins**
```python
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]
```

4. **Set Secure Secret Key**
```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
```

5. **Disable Debug**
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

## API Endpoints (CSRF Exempt)

Some API endpoints remain CSRF exempt for external access:

```python
# In urls_participant.py
@csrf_exempt
def simple_register_api(request):
    # Public API endpoint - no CSRF required
    ...
```

This is intentional for:
- Mobile app access
- Third-party integrations
- Public API endpoints

Web forms still require CSRF protection.

## Additional Resources

### Documentation
- Django CSRF Protection: https://docs.djangoproject.com/en/stable/ref/csrf/
- Django Authentication: https://docs.djangoproject.com/en/stable/topics/auth/

### Related Files
- `CSRF_FIX_SUMMARY.md` - Detailed fix explanation
- `test_csrf_fix.py` - Automated test script
- `event_project/settings_participant.py` - Participant settings
- `event_project/urls_participant.py` - Participant URLs
- `templates/participant/login.html` - Login template
- `templates/participant/signup.html` - Signup template

## Success Criteria

✅ No CSRF errors on login
✅ No CSRF errors on signup
✅ Users can register successfully
✅ Users can login successfully
✅ New users have role='attendee'
✅ Users are redirected after login/signup
✅ Form errors display properly
✅ Form values preserved on errors
✅ CSRF token in form HTML
✅ CSRF cookie set in browser
✅ Session cookie set in browser

## Support

If you encounter issues:

1. Run the test script: `python test_csrf_fix.py`
2. Check browser console for errors
3. Verify cookies are set in DevTools
4. Check Django logs for errors
5. Review `CSRF_FIX_SUMMARY.md` for detailed explanation

---

**Status**: ✅ Fixed and Verified
**Date**: March 5, 2026
**Version**: 1.0
**Tested**: ✅ Automated tests passing
