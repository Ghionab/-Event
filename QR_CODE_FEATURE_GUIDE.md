# QR Code Registration Feature - User Guide

## What's New? 🎉

After registering for an event, participants now receive:
1. A beautiful confirmation page with their QR code
2. An automatic email with the QR code
3. Easy options to download, print, or resend the QR code

## For Attendees

### Step 1: Register for Event
Navigate to the event registration page and fill out the form:
- Full Name
- Email Address
- Phone Number
- Select Ticket Type (if applicable)

### Step 2: Success Page
After submitting, you'll be redirected to a professional success page showing:

```
┌─────────────────────────────────────────────────────┐
│              ✓ Registration Successful!             │
│            Your ticket has been confirmed           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Event Details              Your Entry Pass         │
│  ─────────────              ───────────────         │
│  🎫 REG-XXXXXXXX            ┌─────────────┐        │
│  👤 John Doe                │             │        │
│  📧 john@example.com        │   QR CODE   │        │
│  🏷️  VIP Ticket             │             │        │
│  ✓ Confirmed                └─────────────┘        │
│                                                     │
│  Important Information:                             │
│  • Confirmation email sent to your inbox           │
│  • Save or print this page                         │
│  • Bring valid ID with QR code                     │
│  • Arrive 15 minutes early                         │
│                                                     │
│  [Print Ticket] [Download QR] [Resend Email]       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Step 3: Check Your Email
You'll receive an email with:
- Event details
- Your QR code (embedded in email)
- Registration number
- Check-in instructions

### Step 4: Event Day
Show your QR code at the entrance:
- From the email on your phone
- From a printed copy
- From a screenshot

## For Event Organizers

### Setting Up QR Code Check-in

1. **Access Check-in Dashboard**
   ```
   Navigate to: Event Management > Check-in
   ```

2. **Scan QR Codes**
   - Use mobile device camera
   - Use QR scanner app
   - Use check-in kiosk

3. **Manual Check-in (Backup)**
   - Search by registration number
   - Search by email
   - Verify attendee identity

### Check-in Process

```
Attendee arrives → Shows QR code → Scan code → 
System looks up registration → Verify identity → 
Mark as checked-in → Welcome attendee!
```

## Features

### 1. Print Ticket
- Click "Print Ticket" button
- Browser print dialog opens
- Print-optimized layout
- Includes QR code and all details

### 2. Download QR Code
- Click "Download QR Code" button
- PNG file downloads automatically
- Filename: `ticket-qr-REG-XXXXXXXX.png`
- Can be saved to phone/computer

### 3. Resend Email
- Click "Resend Email" button
- Confirmation email sent again
- Useful if original email was lost
- Button shows "Email Sent!" on success

### 4. Automatic Email
- Sent immediately after registration
- Beautiful HTML design
- Embedded QR code image
- Plain text fallback for compatibility

## Technical Details

### QR Code Format
- **Type**: PNG image
- **Size**: 250x250 pixels
- **Data**: Unique 16-character code
- **Encoding**: Base64 for web display

### Email Template
- **Subject**: "Your Event Ticket - [Event Name]"
- **From**: Event Team
- **Format**: HTML with plain text fallback
- **Attachments**: None (QR code embedded)

### Security
- Each QR code is unique
- Cannot be duplicated or guessed
- Linked to specific registration
- One-time check-in (prevents reuse)

## URLs

### Success Page
```
http://localhost:8001/registration/success/<registration_id>/
```

### Email API
```
POST http://localhost:8001/api/v1/send-qr-email/
Body: {"registration_id": <id>}
```

### Registration API
```
POST http://localhost:8001/api/v1/register/
Body: {
  "event_id": <id>,
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "1234567890",
  "tickets": []
}
```

## Troubleshooting

### QR Code Not Showing
**Problem**: QR code doesn't display on success page

**Solutions**:
1. Refresh the page
2. Check browser console for errors
3. Ensure qrcode library is installed
4. Verify registration was created successfully

### Email Not Received
**Problem**: Confirmation email not in inbox

**Solutions**:
1. Check spam/junk folder
2. Verify email address is correct
3. Use "Resend Email" button
4. Check email server configuration
5. Contact event organizer

### Can't Download QR Code
**Problem**: Download button doesn't work

**Solutions**:
1. Try different browser
2. Check browser download settings
3. Take screenshot instead
4. Use print function

### Print Layout Issues
**Problem**: Print preview looks wrong

**Solutions**:
1. Use "Print Ticket" button (not browser print)
2. Select "Portrait" orientation
3. Ensure "Background graphics" is enabled
4. Try different browser

## Best Practices

### For Attendees
1. ✅ Save email immediately
2. ✅ Take screenshot of QR code
3. ✅ Print ticket as backup
4. ✅ Arrive early to event
5. ✅ Bring valid ID

### For Organizers
1. ✅ Test QR scanning before event
2. ✅ Have manual check-in backup
3. ✅ Train staff on check-in process
4. ✅ Provide clear signage
5. ✅ Have tech support available

## FAQ

**Q: Can I use the same QR code for multiple people?**
A: No, each registration has a unique QR code.

**Q: What if I lose my QR code?**
A: Use the "Resend Email" button or contact the organizer.

**Q: Can I forward the email to someone else?**
A: The QR code is tied to your registration. Transferring tickets may not be allowed.

**Q: Does the QR code expire?**
A: No, it's valid until the event date.

**Q: Can I check in multiple times?**
A: Typically no, check-in is one-time only.

**Q: What if my phone dies at the event?**
A: Print your ticket beforehand or have a screenshot saved.

**Q: Can I edit my registration after receiving the QR code?**
A: Contact the event organizer for registration changes.

**Q: Is the QR code secure?**
A: Yes, each code is unique and cannot be guessed or duplicated.

## Support

For technical issues:
- Email: support@example.com
- Check documentation: REGISTRATION_QR_CODE_FEATURE.md
- Review server logs for errors

For event-specific questions:
- Contact event organizer directly
- Check event details page
- Review confirmation email
