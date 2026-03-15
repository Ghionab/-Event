# Bulk Registration Sample Formats

## Supported File Types
- **CSV Files**: `.csv` (Comma-separated values)
- **Excel Files**: `.xlsx`, `.xls` (Microsoft Excel)

## File Constraints
- **Maximum File Size**: 20MB
- **Maximum Rows**: 10,000 attendees
- **First Row**: Can contain headers (recommended)

## Required Fields
The system requires these two fields to be mapped:
1. **Attendee Name** - Full name of the participant
2. **Email Address** - Valid email (must be unique)

## Optional Fields
- **Phone Number** - Contact phone number
- **Company/Organization** - Employer or organization name
- **Job Title** - Position or role
- **Ticket Type** - Specific ticket category (if available)

## Sample File Formats

### 1. Basic Format (Minimal Required)
**File**: `sample_attendees_minimal.csv`
```csv
attendee_name,attendee_email
John Doe,john.doe@example.com
Jane Smith,jane.smith@example.com
Bob Johnson,bob.johnson@example.com
Alice Brown,alice.brown@example.com
Charlie Wilson,charlie.wilson@example.com
```

### 2. Standard Format (Recommended)
**File**: `sample_attendees_basic.csv`
```csv
name,email,phone,company,job_title
John Smith,john.smith@example.com,+1-555-0101,Tech Corp,Software Engineer
Sarah Johnson,sarah.johnson@example.com,+1-555-0102,Design Studio,UX Designer
Michael Brown,michael.brown@example.com,+1-555-0103,Marketing Inc,Marketing Manager
Emily Davis,emily.davis@example.com,+1-555-0104,Startup LLC,Product Manager
David Wilson,david.wilson@example.com,+1-555-0105,Consulting Group,Business Analyst
```

### 3. With Ticket Types
**File**: `sample_attendees_with_tickets.csv`
```csv
Full Name,Email Address,Phone Number,Organization,Position,Ticket Type
Alex Thompson,alex.thompson@example.com,555-1001,Innovation Labs,CTO,VIP
Maria Rodriguez,maria.rodriguez@example.com,555-1002,Global Solutions,CEO,VIP
James Wilson,james.wilson@example.com,555-1003,Tech Startup,Developer,General Admission
Rachel Green,rachel.green@example.com,555-1004,Design Agency,Creative Director,General Admission
```

### 4. Comprehensive Format (All Fields)
**File**: `sample_attendees_comprehensive.csv`
```csv
Full Name,Email,Phone,Company,Job Title,Ticket Category,Dietary Restrictions,Special Needs
Alexandra Johnson,alexandra.johnson@techcorp.com,+1-555-2001,TechCorp Industries,Senior Software Engineer,VIP,Vegetarian,None
Benjamin Rodriguez,benjamin.rodriguez@designstudio.com,+1-555-2002,Creative Design Studio,Lead UX Designer,General Admission,None,Wheelchair Access
Catherine Williams,catherine.williams@marketing.com,+1-555-2003,Global Marketing Solutions,Marketing Director,VIP,Gluten-Free,None
```

## Column Name Variations (Auto-Detected)

The system automatically detects common column name variations:

### Name Field
- `name`, `full_name`, `attendee_name`, `participant`, `full name`, `attendee name`

### Email Field
- `email`, `e-mail`, `mail`, `email_address`, `email address`, `e_mail`

### Phone Field
- `phone`, `telephone`, `mobile`, `cell`, `contact`, `phone_number`, `phone number`

### Company Field
- `company`, `organization`, `org`, `employer`, `business`, `organisation`

### Job Title Field
- `job`, `title`, `position`, `role`, `designation`, `job_title`, `job title`

### Ticket Type Field
- `ticket`, `type`, `category`, `pass`, `ticket_type`, `ticket type`, `ticket_category`

## Excel Format Example

You can also use Excel files with the same column structure:

| Full Name | Email Address | Phone | Company | Job Title | Ticket Type |
|-----------|---------------|-------|---------|-----------|-------------|
| John Smith | john@example.com | 555-0101 | Tech Corp | Engineer | VIP |
| Jane Doe | jane@example.com | 555-0102 | Design Co | Designer | General |

## Import Process

1. **Upload File** - Select your CSV or Excel file
2. **Map Columns** - System auto-detects common names, you can adjust mappings
3. **Validate Data** - System checks for errors and duplicates
4. **Configure Options** - Choose duplicate handling and ticket assignment
5. **Execute Import** - Process attendees and create registrations
6. **View Results** - See import summary and any issues

## Tips for Best Results

1. **Use Headers**: Include column names in the first row
2. **Valid Emails**: Ensure all email addresses are properly formatted
3. **Unique Emails**: Each attendee should have a unique email address
4. **Consistent Format**: Keep data format consistent within each column
5. **Clean Data**: Remove empty rows and unnecessary columns
6. **Test Small**: Start with a small file to test the process

## Common Issues to Avoid

- **Missing Required Fields**: Name and email are mandatory
- **Invalid Email Formats**: Use proper email format (user@domain.com)
- **Duplicate Emails**: Each email should appear only once
- **Large Files**: Keep under 20MB and 10,000 rows
- **Special Characters**: Avoid unusual characters that might cause encoding issues
- **Empty Rows**: Remove blank rows from your file

## Download Template

Use the "Download Template" button in the bulk registration wizard to get a pre-formatted CSV file with the correct column headers for your event.