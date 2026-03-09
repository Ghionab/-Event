# Registration QR Code Feature

## Overview
After successful registration on the attendee portal, participants now receive a professional confirmation page with a QR code that can be used for event check-in.

## Features Implemented

### 1. Registration Success Page
- **URL**: `/registration/success/<registration_id>/`
- **Template**: `templates/participant/registration_success.html`
- Beautiful, professional design with:
  - Event details display
  - Registration information
  - Large, scannable QR code
  - Important instructions for attendees
  - Action buttons (Print, Download, Email)

### 2. QR Code Generation
- Automatically generated for each registration
- Stored in `Registration.qr_code` field
- Generated using the `qrcode` library
- Displayed as base64-encoded PNG image
- Contains unique registration identifier for check-in

### 3. Email Confirmation
- Automatic email sent upon registration
- Beautiful HTML email template with:
  - Embedded QR code image
  - Event details
  - Registration information
  - Check-in instructions
- Plain text fallback for email clients
- Resend option available on success page

### 4. API Endpoints

#### Registration API
- **Endpoint**: `POST /api/v1/register/`
- **Response**: Now includes `success_url` field
- **Behavior**: 
  - Form submissions: Redirects to success page
  - JSON requests: Returns registration data with success URL

#### Email API
- **Endpoint**: `POST /api/v1/send-qr-email/`
- **CSRF**: Exempt (public API)
- **Payload**: `{"registration_id": <id>}`
- **Response**: `{"success": true/false, "message": "..."}`

## User Flow

1. **Registration**
   - User fills out registration form
   - Submits to `/api/v1/register/`
   - Registration created with unique QR code

2. **Success Page**
   - Automatically redirected to `/registration/success/<id>/`
   - QR code displayed prominently
   - Confirmation email sent automatically

3. **Email Confirmation**
   - Participant receives email with QR code
   - Can save/print email for event day
   - Email includes all event details

4. **Event Day**
   - Participant shows QR code (from email or success page)
   - Organizer scans QR code for check-in
   - Quick and efficient entry process

## Technical Details

### Files Modified/Created

1. **templates/participant/registration_success.html** (NEW)
   - Professional success page template
   - Responsive design with Tailwind CSS
   - Print-friendly styling
   - Interactive buttons for download/email

2. **registration/views_success.py** (NEW)
   - `registration_success()` - Renders success page
   - `send_qr_email()` - API endpoint for email
   - `send_qr_email_direct()` - Helper for automatic email

3. **events_api/views/simple_registration.py** (MODIFIED)
   - Added automatic email sending
   - Redirects to success page for form submissions
   - Returns success_url in JSON response

4. **registration/views.py** (MODIFIED)
   - Updated `registration_success()` to include QR code

5. **event_project/urls_participant.py** (MODIFIED)
   - Added `/api/v1/send-qr-email/` endpoint

6. **templates/participant/register.html** (MODIFIED)
   - Updated JavaScript to use success_url from API

### QR Code Format
- **Data**: `Registration.qr_code` (16-character hex string)
- **Format**: PNG image, base64-encoded
- **Size**: 250x250 pixels (configurable)
- **Error Correction**: Low (can be increased if needed)

### Email Configuration
Requires Django email settings in `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Event Team <noreply@example.com>'
```

## Usage Examples

### For Attendees

1. **Register for Event**
   ```
   Navigate to: http://localhost:8001/events/<event_id>/register/
   Fill form and submit
   ```

2. **View Success Page**
   ```
   Automatically redirected to success page
   QR code displayed
   Email sent automatically
   ```

3. **Download QR Code**
   ```
   Click "Download QR Code" button
   Saves as: ticket-qr-REG-XXXXXXXX.png
   ```

4. **Resend Email**
   ```
   Click "Resend Email" button
   Confirmation email sent again
   ```

### For Organizers

1. **Check-in with QR Code**
   ```
   Scan QR code at event entrance
   System looks up registration by qr_code field
   Mark as checked-in
   ```

2. **Manual Check-in**
   ```
   Search by registration number or email
   Verify attendee identity
   Mark as checked-in
   ```

## Security Considerations

1. **QR Code Uniqueness**
   - Each registration has unique 16-character hex code
   - Collision probability: ~1 in 18 quintillion

2. **Email Verification**
   - Email sent to registered email address only
   - No authentication required for success page (by design)
   - Registration ID is not guessable

3. **API Security**
   - Registration API is CSRF-exempt (public endpoint)
   - Email API is CSRF-exempt (public endpoint)
   - Rate limiting recommended for production

## Future Enhancements

1. **SMS Notifications**
   - Send QR code via SMS
   - Requires SMS gateway integration

2. **Mobile Wallet Integration**
   - Apple Wallet pass
   - Google Pay pass

3. **QR Code Customization**
   - Event branding/logo in QR code
   - Color customization

4. **Advanced Check-in**
   - Mobile app for QR scanning
   - Real-time check-in analytics
   - Duplicate scan prevention

5. **Multi-language Support**
   - Translate email templates
   - Localized success page

## Testing

### Manual Testing Steps

1. **Test Registration Flow**
   ```bash
   # Start server
   python manage.py runserver 8001
   
   # Navigate to registration page
   # Fill form and submit
   # Verify redirect to success page
   # Check QR code displays
   ```

2. **Test Email Sending**
   ```bash
   # Check email inbox
   # Verify QR code in email
   # Test resend button
   ```

3. **Test QR Code Download**
   ```bash
   # Click download button
   # Verify PNG file downloaded
   # Open and verify QR code
   ```

4. **Test Print Functionality**
   ```bash
   # Click print button
   # Verify print preview
   # Check layout is print-friendly
   ```

### API Testing

```bash
# Test registration API
curl -X POST http://localhost:8001/api/v1/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "tickets": []
  }'

# Test email API
curl -X POST http://localhost:8001/api/v1/send-qr-email/ \
  -H "Content-Type: application/json" \
  -d '{"registration_id": 1}'
```

## Troubleshooting

### Email Not Sending
- Check Django email settings
- Verify SMTP credentials
- Check spam folder
- Review server logs for errors

### QR Code Not Displaying
- Verify qrcode library installed: `pip install qrcode[pil]`
- Check browser console for errors
- Verify base64 encoding is correct

### Success Page Not Loading
- Check URL configuration
- Verify registration ID exists
- Check template path

## Support

For issues or questions:
- Check server logs: `python manage.py runserver`
- Review Django debug toolbar
- Contact: support@example.com
