# Gate Staff Portal - Quick Start Checklist

## ✅ Pre-Launch Checklist

### 1. Installation Verification
- [ ] Run `python test_staff_portal.py`
- [ ] Verify all tests pass
- [ ] Check that STAFF role exists in database
- [ ] Confirm migrations are applied

### 2. User Setup
- [ ] Create at least one staff user
- [ ] Test staff login credentials
- [ ] Verify role-based access control works
- [ ] Create organizer/admin users if needed

### 3. Test Data
- [ ] Create at least one active event (today or future)
- [ ] Add ticket types to events
- [ ] Create test registrations (5-10 minimum)
- [ ] Generate QR codes for registrations

### 4. Portal Testing
- [ ] Start staff portal: `python run_staff_portal.py`
- [ ] Access http://localhost:8002
- [ ] Login with staff credentials
- [ ] Verify staff badge displays correctly
- [ ] Check event list shows active events

### 5. QR Scanner Testing
- [ ] Open event dashboard
- [ ] Click "Start Scanning"
- [ ] Grant camera permissions
- [ ] Test QR code scanning
- [ ] Verify check-in success message
- [ ] Check statistics update

### 6. Manual Check-in Testing
- [ ] Search for attendee by name
- [ ] Search for attendee by email
- [ ] Search for attendee by registration number
- [ ] Click "Check In" button
- [ ] Verify confirmation dialog
- [ ] Check UI updates after check-in

### 7. Statistics Testing
- [ ] Verify Total Registered counter
- [ ] Verify Total Checked In counter
- [ ] Verify Check-in Rate percentage
- [ ] Wait 30 seconds for auto-refresh
- [ ] Check stats update correctly

### 8. Mobile Testing
- [ ] Test on mobile device (iOS/Android)
- [ ] Verify responsive layout
- [ ] Test camera access on mobile
- [ ] Test touch interactions
- [ ] Verify no horizontal scrolling

### 9. Security Testing
- [ ] Try accessing portal without login
- [ ] Try accessing with attendee role
- [ ] Verify CSRF protection works
- [ ] Check session timeout (8 hours)
- [ ] Test logout functionality

### 10. Error Handling
- [ ] Test invalid QR code
- [ ] Test already checked-in attendee
- [ ] Test network error scenarios
- [ ] Verify error messages display
- [ ] Check console for JavaScript errors

---

## 🚀 Launch Day Checklist

### Before Event Starts

#### 1. System Preparation
- [ ] Start all three portals
  - [ ] Organizer: `python manage.py runserver 8000`
  - [ ] Participant: `python manage.py runserver 8001 --settings=event_project.settings_participant`
  - [ ] Staff: `python run_staff_portal.py`
- [ ] Verify database backup exists
- [ ] Check server resources (CPU, memory, disk)
- [ ] Test internet connectivity

#### 2. Staff Preparation
- [ ] Distribute staff login credentials
- [ ] Brief staff on portal usage
- [ ] Show QR scanner demo
- [ ] Explain manual check-in process
- [ ] Provide troubleshooting guide

#### 3. Equipment Check
- [ ] Tablets/phones charged
- [ ] Camera permissions granted
- [ ] Backup devices ready
- [ ] Internet connection stable
- [ ] Power outlets available

#### 4. Event Configuration
- [ ] Verify event is published
- [ ] Check registration count
- [ ] Confirm ticket types are correct
- [ ] Test sample QR code
- [ ] Review attendee list

### During Event

#### Staff Operations
- [ ] Staff logged in to portal
- [ ] Event selected in dashboard
- [ ] QR scanner ready
- [ ] Statistics monitoring active
- [ ] Backup staff available

#### Monitoring
- [ ] Check-in rate tracking
- [ ] Watch for errors/issues
- [ ] Monitor queue length
- [ ] Track peak times
- [ ] Note any problems

#### Troubleshooting
- [ ] Backup manual check-in ready
- [ ] Printed attendee list available
- [ ] Technical support on standby
- [ ] Alternative devices ready
- [ ] Escalation process defined

### After Event

#### Data Verification
- [ ] Review total check-ins
- [ ] Compare with expected attendance
- [ ] Check for duplicate check-ins
- [ ] Verify all data saved
- [ ] Export check-in report

#### System Cleanup
- [ ] Log out all staff users
- [ ] Stop portal servers
- [ ] Backup database
- [ ] Archive logs
- [ ] Document issues

#### Review
- [ ] Staff feedback collection
- [ ] Performance analysis
- [ ] Issue documentation
- [ ] Improvement suggestions
- [ ] Update procedures

---

## 📋 Daily Operations Checklist

### Morning Setup (30 minutes before)
- [ ] Start staff portal
- [ ] Test login
- [ ] Verify event data loaded
- [ ] Test QR scanner
- [ ] Check statistics display
- [ ] Brief staff team

### During Operations
- [ ] Monitor check-in flow
- [ ] Assist with issues
- [ ] Track statistics
- [ ] Manage queue
- [ ] Communicate with organizers

### End of Day
- [ ] Review check-in totals
- [ ] Export data
- [ ] Log out staff
- [ ] Stop portal
- [ ] Report to organizers

---

## 🔧 Troubleshooting Checklist

### Camera Not Working
- [ ] Check browser permissions
- [ ] Try different browser (Chrome recommended)
- [ ] Restart device
- [ ] Check camera hardware
- [ ] Use manual check-in as backup

### Check-in Fails
- [ ] Verify registration status (must be "confirmed")
- [ ] Check user role (staff/organizer/admin)
- [ ] Verify internet connection
- [ ] Check API endpoint
- [ ] Review browser console errors

### Statistics Not Updating
- [ ] Check network connection
- [ ] Verify API endpoint accessible
- [ ] Refresh page manually
- [ ] Check browser console
- [ ] Restart portal if needed

### Login Issues
- [ ] Verify email address
- [ ] Check password
- [ ] Confirm user role (staff/organizer/admin)
- [ ] Check session timeout
- [ ] Clear browser cache

### QR Code Not Scanning
- [ ] Improve lighting
- [ ] Clean camera lens
- [ ] Hold QR code steady
- [ ] Adjust distance
- [ ] Use manual check-in

---

## 📱 Mobile Device Checklist

### iOS Setup
- [ ] Safari browser (recommended)
- [ ] Camera permission granted
- [ ] Location services enabled (if needed)
- [ ] Auto-lock disabled
- [ ] Brightness increased

### Android Setup
- [ ] Chrome browser (recommended)
- [ ] Camera permission granted
- [ ] Location services enabled (if needed)
- [ ] Stay awake enabled
- [ ] Brightness increased

### General Mobile
- [ ] Device fully charged
- [ ] Backup battery available
- [ ] Screen protector clean
- [ ] Case doesn't block camera
- [ ] Test mode enabled

---

## 🎯 Performance Checklist

### Speed Optimization
- [ ] Page loads in < 2 seconds
- [ ] QR scan responds in < 1 second
- [ ] Check-in API < 500ms
- [ ] Stats refresh every 30 seconds
- [ ] No lag in UI updates

### Capacity Testing
- [ ] Test with 10+ concurrent staff
- [ ] Test with 100+ registrations
- [ ] Test rapid check-ins (10/minute)
- [ ] Monitor server resources
- [ ] Check database performance

### User Experience
- [ ] UI is intuitive
- [ ] Buttons are touch-friendly
- [ ] Text is readable
- [ ] Colors are clear
- [ ] Feedback is immediate

---

## 🔒 Security Checklist

### Access Control
- [ ] Only authorized roles can access
- [ ] Session timeout configured (8 hours)
- [ ] CSRF protection enabled
- [ ] Passwords are strong
- [ ] Credentials are secure

### Data Protection
- [ ] HTTPS enabled (production)
- [ ] Database encrypted
- [ ] Backups scheduled
- [ ] Audit logs enabled
- [ ] PII protected

### Compliance
- [ ] Privacy policy reviewed
- [ ] Data retention policy set
- [ ] User consent obtained
- [ ] GDPR compliance (if applicable)
- [ ] Security audit completed

---

## 📊 Reporting Checklist

### Real-time Reports
- [ ] Check-in rate
- [ ] Total registered
- [ ] Total checked in
- [ ] Recent check-ins
- [ ] Peak times

### Post-Event Reports
- [ ] Final attendance count
- [ ] Check-in timeline
- [ ] Staff performance
- [ ] Issue log
- [ ] Recommendations

### Data Export
- [ ] Registration list
- [ ] Check-in log
- [ ] Statistics summary
- [ ] Audit trail
- [ ] Error log

---

## ✨ Best Practices Checklist

### Staff Training
- [ ] Portal navigation
- [ ] QR scanning technique
- [ ] Manual check-in process
- [ ] Error handling
- [ ] Customer service

### Communication
- [ ] Staff briefing completed
- [ ] Organizer coordination
- [ ] Issue escalation path
- [ ] Emergency contacts
- [ ] Feedback channels

### Documentation
- [ ] User guide available
- [ ] Command reference handy
- [ ] Troubleshooting guide ready
- [ ] Contact list updated
- [ ] Procedures documented

---

## 🎉 Success Criteria

### Technical Success
- [ ] 99%+ uptime during event
- [ ] < 1% error rate
- [ ] < 2 second average check-in time
- [ ] Zero data loss
- [ ] All features working

### Operational Success
- [ ] Staff trained and confident
- [ ] Smooth check-in flow
- [ ] Minimal queue times
- [ ] Quick issue resolution
- [ ] Positive staff feedback

### Business Success
- [ ] Accurate attendance tracking
- [ ] Real-time statistics
- [ ] Audit trail complete
- [ ] Organizer satisfaction
- [ ] Attendee satisfaction

---

## 📞 Emergency Contacts

### Technical Support
- [ ] System administrator: _______________
- [ ] Database admin: _______________
- [ ] Network support: _______________

### Event Support
- [ ] Event organizer: _______________
- [ ] Venue manager: _______________
- [ ] Security team: _______________

### Escalation
- [ ] Level 1 (Staff): _______________
- [ ] Level 2 (Supervisor): _______________
- [ ] Level 3 (Admin): _______________

---

## 📝 Notes Section

### Pre-Event Notes
```
Date: _______________
Event: _______________
Staff Count: _______________
Expected Attendance: _______________
Special Instructions: _______________
```

### Issue Log
```
Time | Issue | Resolution | Staff
-----|-------|------------|------
     |       |            |
     |       |            |
     |       |            |
```

### Feedback
```
What went well:
_______________________________________________
_______________________________________________

What needs improvement:
_______________________________________________
_______________________________________________

Action items:
_______________________________________________
_______________________________________________
```

---

**Remember**: The goal is smooth, efficient check-in that enhances the attendee experience!

**Status**: Ready for deployment ✅
**Version**: 1.0.0
**Last Updated**: March 11, 2026
