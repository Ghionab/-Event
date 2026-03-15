# Testing Check-in Functionality

## Quick Start

### 1. Start the Staff Portal
```bash
python manage.py runserver 8002 --settings=event_project.settings_staff
```

### 2. Login
- Navigate to: http://localhost:8002/staff/login/
- Use your staff credentials

### 3. Access Event Dashboard
- Click on an event from the list
- Or go directly to: http://localhost:8002/staff/events/1/

## Testing QR Code Scanning

### Option A: Use Generated QR Codes (Recommended)

1. **Generate QR codes**:
   ```bash
   python generate_test_qr.py
   ```
   This creates PNG files like `qr_REG-E560E8D4.png`

2. **Display QR code on another device**:
   - Open the PNG file on your phone or another screen
   - Or print it out

3. **Scan with staff portal**:
   - Click "Start Scanning" button
   - Point camera at the QR code
   - Should see success message immediately

### Option B: Use Registration Success Page

1. **Create a test registration**:
   - Go to participant portal: http://localhost:8001
   - Register for an event
   - After registration, you'll see a QR code

2. **Scan the QR code**:
   - Display it on your phone
   - Scan with staff portal camera

## Testing Manual Check-in

1. **Find an attendee** in the list on the event dashboard
2. **Click "Check In"** button next to their name
3. **Confirm** the check-in in the popup
4. **Verify**:
   - Status changes to "CHECKED IN"
   - Button becomes disabled
   - Stats update automatically
   - Green background appears on the card

## Verification Steps

### Check Database
```bash
python manage.py shell --settings=event_project.settings_staff
```

```python
from registration.models import Registration, CheckIn

# Check registration status
reg = Registration.objects.get(id=23)
print(f"Status: {reg.status}")
print(f"Checked in at: {reg.checked_in_at}")

# Check check-in log
checkins = CheckIn.objects.filter(registration=reg)
for ci in checkins:
    print(f"Method: {ci.method}, Time: {ci.check_in_time}")
```

### Check API Response
```bash
# Test registrations list
curl http://localhost:8002/api/v1/events/1/registrations/

# Test check-in (requires session cookie)
curl -X POST http://localhost:8002/api/v1/events/1/registrations/23/check-in/ \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

## Expected Behavior

### Successful Check-in
- ✅ Green success alert appears
- ✅ Attendee card gets green background
- ✅ Status badge changes to "CHECKED IN"
- ✅ Check-in button becomes disabled
- ✅ Stats update (total checked in increases)
- ✅ Check-in rate percentage updates

### Already Checked In
- ⚠️ Warning alert: "Already checked in"
- ⚠️ Shows previous check-in time
- ⚠️ No changes to database

### Invalid QR Code
- ❌ Error alert: "Invalid QR code or registration not found"
- ❌ No changes to database

## Troubleshooting

### Camera Not Working
- **Check browser permissions**: Allow camera access
- **Try different browser**: Chrome/Edge work best
- **Check HTTPS**: Camera requires HTTPS (or localhost)

### API Errors
- **Check server is running**: Port 8002
- **Check console**: F12 → Console tab for errors
- **Check network**: F12 → Network tab for failed requests

### QR Code Not Scanning
- **Ensure good lighting**: QR codes need clear visibility
- **Check QR code size**: Should be at least 2x2 inches
- **Try different distance**: Move camera closer/farther
- **Check QR code data**: Should match registration.qr_code

### Stats Not Updating
- **Refresh page**: F5 to reload
- **Check JavaScript console**: Look for errors
- **Verify API endpoint**: Should return updated counts

## Test Scenarios

### Scenario 1: First-time Check-in
1. Find confirmed registration
2. Scan QR code
3. Verify success message
4. Check database for CheckIn record

### Scenario 2: Duplicate Check-in
1. Check in same person twice
2. Should show "already checked in" warning
3. Verify no duplicate CheckIn records

### Scenario 3: Manual Check-in
1. Use check-in button instead of QR
2. Verify same behavior as QR scan
3. Check method is "manual" in database

### Scenario 4: Search and Check-in
1. Use search box to find attendee
2. Check in from search results
3. Verify stats update correctly

### Scenario 5: Multiple Staff Members
1. Login on two different devices
2. Check in different people simultaneously
3. Verify both check-ins work
4. Check stats sync across devices

## Performance Testing

### Load Test
```bash
# Check-in 100 people rapidly
python test_bulk_checkin.py
```

### Concurrent Access
- Open staff portal on multiple devices
- Check in different people at same time
- Verify no race conditions

## Security Testing

### Test Invalid Scenarios
1. Try checking in cancelled registration
2. Try checking in pending registration
3. Try checking in with invalid event ID
4. Try checking in with invalid registration ID

All should return appropriate error messages.

## Success Criteria

✅ QR scanner activates camera
✅ QR codes scan successfully
✅ Check-in updates database immediately
✅ UI updates without page refresh
✅ Stats refresh automatically
✅ Manual check-in button works
✅ Duplicate check-ins prevented
✅ Error messages display clearly
✅ CheckIn records created with correct method
✅ Multiple staff can check in simultaneously

## Files to Monitor

- `staff/views.py` - Manual check-in logic
- `events_api/views.py` - API check-in logic
- `staff/templates/staff/event_dashboard.html` - UI and JavaScript
- `registration/models.py` - Registration and CheckIn models

## Logs to Check

```bash
# Django logs
tail -f logs/staff_portal.log

# Check-in activity
python manage.py shell --settings=event_project.settings_staff
>>> from registration.models import CheckIn
>>> CheckIn.objects.order_by('-check_in_time')[:10]
```
