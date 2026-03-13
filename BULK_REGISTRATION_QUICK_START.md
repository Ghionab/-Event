# Bulk Registration - Quick Start Guide

## 🚀 How to Access

### Method 1: From Event Detail Page
1. Go to **Organizer Portal**
2. Click on your **Event**
3. Click **"Manage Registrations"** button
4. Click **"Bulk Upload"** button

### Method 2: From Registrations Tab
1. Go to **Organizer Portal**
2. Click **"Registrations"** in sidebar
3. Select your event from the list
4. Click **"Bulk Upload"** button in the header

---

## 📝 How to Use

### Step 1: Prepare Your File

Download the CSV template or create your own file with these columns:

**Required Columns:**
- `name` - Full name of attendee
- `email` - Email address (must be unique)

**Optional Columns:**
- `phone` - Phone number
- `company` - Company name
- `job_title` - Job title

**Example CSV:**
```csv
name,email,phone,company,job_title
John Doe,john@example.com,+1234567890,Acme Inc,Developer
Jane Smith,jane@example.com,+0987654321,Tech Corp,Manager
Bob Johnson,bob@example.com,+1122334455,StartUp Co,CEO
```

### Step 2: Upload Your File

1. **Select File Format**
   - Choose Excel (.xlsx, .xls) or CSV (.csv)

2. **Upload File**
   - Click the upload area or drag and drop your file
   - Maximum file size: 5MB

3. **Configure Options**
   - ✅ First row contains headers (check if your file has column names)
   - ✅ Send invitation emails (check to email all attendees)

4. **Submit**
   - Click "Upload and Process" button

### Step 3: Review Results

After upload, you'll see:
- **Total rows** processed
- **Success count** - registrations created
- **Error count** - rows that failed
- **Status** - completed, failed, or processing

Click "View Details" to see:
- Individual row results
- Error messages for failed rows
- Registration numbers for successful rows

---

## ✅ What Happens During Upload

1. **File Validation**
   - Checks file type (.xlsx, .xls, .csv)
   - Validates file size (max 5MB)

2. **Data Processing**
   - Reads file content
   - Extracts attendee information
   - Validates required fields (name, email)

3. **Registration Creation**
   - Checks for duplicate emails
   - Creates registration records
   - Assigns default ticket type
   - Updates ticket counts

4. **Email Notifications** (if enabled)
   - Sends confirmation emails
   - Includes event details
   - Provides registration number

5. **Result Tracking**
   - Records success/error counts
   - Stores error messages
   - Creates upload history entry

---

## 🎯 Best Practices

### Before Upload
- ✅ Remove empty rows
- ✅ Ensure email addresses are unique
- ✅ Validate email formats
- ✅ Use consistent formatting
- ✅ Test with small file first

### During Upload
- ✅ Check "First row contains headers" if applicable
- ✅ Enable "Send invitation emails" for automatic notifications
- ✅ Wait for processing to complete

### After Upload
- ✅ Review upload history
- ✅ Check success/error counts
- ✅ View details for any errors
- ✅ Fix errors and re-upload if needed

---

## ⚠️ Common Issues & Solutions

### Issue: "Email already registered"
**Solution:** Remove duplicate emails from your file or check existing registrations

### Issue: "Name and email are required"
**Solution:** Ensure all rows have both name and email filled in

### Issue: "No active ticket type available"
**Solution:** Create and activate at least one ticket type for your event

### Issue: "File type not allowed"
**Solution:** Use only .xlsx, .xls, or .csv files

### Issue: "File size cannot exceed 5MB"
**Solution:** Split your file into smaller batches or remove unnecessary columns

---

## 📊 Upload History

The upload history table shows:
- **Date & Time** - When the upload was performed
- **File Name** - Original filename and size
- **Total** - Total rows in the file
- **Success** - Number of successful registrations
- **Errors** - Number of failed rows
- **Status** - Current processing status
- **Actions** - View details button

---

## 🔗 Related Features

### Manual Registration
- Add individual attendees manually
- Access from Registrations tab
- Click "Add Attendee" button

### Registration List
- View all registrations
- Filter by status
- Export to Excel/CSV
- Generate QR codes

### Ticket Management
- Create ticket types
- Set prices and quantities
- Configure sales periods
- Track sales

---

## 💡 Tips for Large Events

### For 100-500 Attendees
- Upload in single batch
- Enable email notifications
- Review results immediately

### For 500-1,000 Attendees
- Consider splitting into 2-3 batches
- Test with small batch first
- Monitor email delivery

### For 1,000+ Attendees
- Split into multiple batches (500 each)
- Upload during off-peak hours
- Disable email notifications initially
- Send emails separately if needed

---

## 📞 Support

If you encounter issues:
1. Check the upload history for error details
2. Review this guide for common solutions
3. Verify your file format matches the template
4. Contact system administrator if problems persist

---

## 🎉 Success!

Once your bulk upload is complete:
- ✅ All attendees are registered
- ✅ Tickets are assigned
- ✅ Emails are sent (if enabled)
- ✅ QR codes are generated
- ✅ Registration numbers are created

You can now:
- View registrations in the Registrations tab
- Download QR codes for check-in
- Export registration list
- Send additional communications

---

**Quick Links:**
- [Bulk Registration Overview](BULK_REGISTRATION_OVERVIEW.md)
- [Improvements Made](BULK_REGISTRATION_IMPROVEMENTS.md)
- [Technical Documentation](TECHNICAL_DOCUMENTATION.md)

---

**Last Updated:** March 13, 2026
