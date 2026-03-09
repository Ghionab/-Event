# QR Code Registration - Quick Start Guide

## 🚀 Ready to Use!

Your QR code registration feature is now complete and ready to test.

## Test It Now

### Step 1: Start Server
```bash
python manage.py runserver 8001
```

### Step 2: Register for Event
1. Open browser: `http://localhost:8001/events/`
2. Click on any event
3. Click "Register" button
4. Fill out the form:
   - Full Name: John Doe
   - Email: your-email@example.com
   - Phone: 1234567890
5. Click "Complete Registration"

### Step 3: View Success Page
You'll be automatically redirected to a page showing:
- ✅ Your registration number (REG-XXXXXXXX)
- ✅ Event details
- ✅ A large QR code
- ✅ Buttons to print, download, or email

### Step 4: Check Email (Optional)
If email is configured, check your inbox for:
- Subject: "Your Event Ticket - [Event Name]"
- Contains: QR code and event details

## Quick Test URLs

Based on your existing registrations:

```
http://localhost:8001/registration/success/22/
http://localhost:8001/registration/success/23/
http://localhost:8001/registration/success/24/
```

## What You'll See

### Success Page Layout:
```
┌────────────────────────────────────────────────────────┐
│                    ✓ Success Icon                      │
│          Registration Successful!                      │
│         Your ticket has been confirmed                 │
├────────────────────────────────────────────────────────┤
│                                                        │
│  [Event Title]                                         │
│  📅 Date  🕐 Time  📍 Venue                           │
│                                                        │
│  ┌─────────────────────┐  ┌──────────────────┐       │
│  │ Registration Details│  │  Your Entry Pass │       │
│  │                     │  │                  │       │
│  │ 🎫 REG-XXXXXXXX    │  │   ┌──────────┐   │       │
│  │ 👤 John Doe        │  │   │          │   │       │
│  │ 📧 john@email.com  │  │   │ QR CODE  │   │       │
│  │ 🏷️  VIP Ticket     │  │   │          │   │       │
│  │ ✓ Confirmed        │  │   └──────────┘   │       │
│  └─────────────────────┘  └──────────────────┘       │
│                                                        │
│  ℹ️ Important Information                             │
│  • Confirmation email sent                            │
│  • Save or print this page                            │
│  • Bring valid ID with QR code                        │
│  • Arrive 15 minutes early                            │
│                                                        │
│  [Print Ticket] [Download QR] [Resend Email] [Back]  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Features to Test

### 1. Print Ticket
- Click "Print Ticket"
- Print dialog opens
- Layout is optimized for printing
- QR code is clearly visible

### 2. Download QR Code
- Click "Download QR Code"
- PNG file downloads
- Filename: `ticket-qr-REG-XXXXXXXX.png`
- Can be opened and scanned

### 3. Resend Email
- Click "Resend Email"
- Button shows "Sending..."
- Changes to "Email Sent!" on success
- Check your inbox

### 4. Responsive Design
- Resize browser window
- Layout adapts to screen size
- Works on mobile devices
- QR code remains scannable

## Email Configuration (Optional)

To enable email sending, add to `event_project/settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Event Team <noreply@example.com>'
```

### For Gmail:
1. Enable 2-factor authentication
2. Generate app password: https://myaccount.google.com/apppasswords
3. Use app password in EMAIL_HOST_PASSWORD

### For Testing (No Real Emails):
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
This prints emails to console instead of sending.

## API Testing

### Test Registration API:
```bash
curl -X POST http://localhost:8001/api/v1/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "full_name": "Test User",
    "email": "test@example.com",
    "phone": "1234567890",
    "tickets": []
  }'
```

Expected response:
```json
{
  "id": 25,
  "registration_number": "REG-XXXXXXXX",
  "message": "Registration successful!",
  "status": "confirmed",
  "total_amount": "0.00",
  "success_url": "/registration/success/25/"
}
```

### Test Email API:
```bash
curl -X POST http://localhost:8001/api/v1/send-qr-email/ \
  -H "Content-Type: application/json" \
  -d '{"registration_id": 22}'
```

Expected response:
```json
{
  "success": true,
  "message": "Email sent successfully"
}
```

## Run Tests

```bash
python test_qr_registration.py
```

Expected output:
```
🚀 Starting QR Code Registration Feature Tests

============================================================
Testing QR Code Generation
============================================================
✓ Found 5 registrations
✓ QR code generated successfully (620 bytes)
...
✅ All tests passed!
```

## Troubleshooting

### QR Code Not Showing
```bash
# Install qrcode library
pip install qrcode[pil]

# Verify installation
python -c "import qrcode; print('QR code library installed')"
```

### Email Not Sending
```bash
# Check email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Success Page 404
```bash
# Check URL configuration
python manage.py show_urls | grep success

# Should show:
# /registration/success/<int:registration_id>/
```

## Next Steps

1. ✅ Test the success page
2. ✅ Configure email (optional)
3. ✅ Test email sending
4. ✅ Test QR code download
5. ✅ Test print functionality
6. ✅ Test on mobile device
7. ✅ Review documentation

## Documentation Files

- `IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `REGISTRATION_QR_CODE_FEATURE.md` - Technical documentation
- `QR_CODE_FEATURE_GUIDE.md` - User guide
- `QUICK_START.md` - This file

## Support

Everything is working! The tests passed successfully:
- ✅ QR code generation
- ✅ Email function
- ✅ Success page data
- ✅ API response format

Just configure email settings and you're ready to go! 🎉
