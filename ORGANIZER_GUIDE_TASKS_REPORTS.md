# Organizer Guide: Task Management & Reports

## Quick Start Guide for Event Organizers

This guide will help you use the enhanced Task Management and Report systems to efficiently manage your events.

---

## 📋 Task Management

### Overview
The Task Management system helps you organize and track all tasks related to your events. You can assign tasks to team members, track progress, set priorities, and monitor deadlines.

### Accessing Tasks
1. Log in to the Organizer Portal (http://localhost:8000)
2. Navigate to **Advanced** → **Tasks** or visit `/advanced/tasks/`

### Creating a Task

#### Method 1: From Task List
1. Go to `/advanced/tasks/`
2. Click **Create New Task**
3. Fill in the form:
   - **Event**: Select the event this task belongs to
   - **Title**: Brief description (e.g., "Book venue")
   - **Description**: Detailed information
   - **Assigned To**: Select a team member
   - **Status**: To Do, In Progress, Review, Completed, or Cancelled
   - **Priority**: Low, Medium, High, or Urgent
   - **Due Date**: When the task should be completed
   - **Progress %**: 0-100% completion
   - **Estimated Hours**: How long you think it will take
   - **Tags**: Comma-separated tags (e.g., "venue, logistics, urgent")
   - **Attachment**: Upload related files
4. Click **Save**

#### Method 2: From Event Page
1. Visit `/advanced/tasks/create/?event=1` (replace 1 with your event ID)
2. The event will be pre-selected
3. Fill in the remaining fields

### Viewing Tasks

#### Task List View
The task list shows all your tasks with:
- **Statistics Dashboard**: Total, To Do, In Progress, Completed, Overdue counts
- **Filters**: Filter by event, status, priority, assigned team member
- **Search**: Search by title, description, or tags
- **Sorting**: Sort by priority, due date, or creation date

#### Task Detail View
Click on any task to see:
- Full task details
- Progress tracking
- Time estimates vs actual
- Comments from team members
- Attachment downloads
- Dependency information

### Updating Tasks

1. Click on a task to view details
2. Click **Edit Task**
3. Update any fields
4. Click **Save**

**Quick Actions:**
- Mark as completed
- Change status
- Update progress percentage
- Add comments

### Task Comments
Team members can collaborate on tasks:
1. Open task detail page
2. Scroll to **Comments** section
3. Type your comment
4. Click **Add Comment**

### Bulk Operations

Select multiple tasks and perform actions:

1. Go to task list
2. Check the boxes next to tasks you want to update
3. Select an action from the dropdown:
   - **Mark as Completed**: Set all selected tasks to completed
   - **Change Status**: Update status for all selected tasks
   - **Change Priority**: Update priority for all selected tasks
   - **Delete**: Remove all selected tasks
4. Click **Apply**

### Exporting Tasks

Export your tasks to CSV for external analysis:

1. Go to `/advanced/tasks/`
2. Apply any filters you want (event, status, priority)
3. Click **Export to CSV**
4. Open the downloaded file in Excel or Google Sheets

**CSV includes:**
- Event name
- Task title and description
- Status and priority
- Assigned team member
- Due date and completion date
- Progress percentage
- Time estimates and actuals
- Tags

### Task Best Practices

✅ **Use Clear Titles**: "Book venue for Tech Conference 2026"
✅ **Set Realistic Due Dates**: Give team members enough time
✅ **Update Progress Regularly**: Keep the team informed
✅ **Use Tags**: Makes filtering easier (e.g., "urgent", "venue", "catering")
✅ **Track Time**: Log estimated and actual hours for future planning
✅ **Add Comments**: Keep communication in one place
✅ **Set Dependencies**: Link tasks that depend on each other

---

## 📊 Report System

### Overview
The Report system generates comprehensive reports about your events with multiple export formats (CSV, Excel, PDF).

### Accessing Reports
1. Log in to the Organizer Portal
2. Navigate to **Business** → **Reports** or visit `/business/reports/`

### Creating a Report

1. Go to `/business/reports/`
2. Click **Create New Report**
3. Fill in the form:
   - **Event**: Select the event
   - **Name**: Report name (e.g., "Registration Summary Q1 2026")
   - **Report Type**: Choose from:
     - Registration Report
     - Revenue Report
     - Attendance Report
     - Engagement Report
     - Sponsor Report
     - Expense Report
   - **Export Format**: CSV, Excel, or PDF (default format)
   - **Filters**: JSON filters (optional, e.g., `{"status": "confirmed"}`)
   - **Scheduled**: Enable for automated reports
   - **Frequency**: Daily, Weekly, or Monthly
4. Click **Save**

### Report Types

#### 1. Registration Report
Shows all registrations with:
- Registration number
- Attendee name and email
- Status (confirmed, pending, cancelled)
- Ticket type
- Amount paid
- Registration date

**Use Case**: Track who registered, when, and their status

#### 2. Revenue Report
Shows revenue breakdown by:
- Ticket type
- Quantity sold
- Total revenue per ticket type

**Use Case**: Understand which ticket types generate the most revenue

#### 3. Attendance Report
Shows attendance statistics:
- Status distribution (confirmed, checked-in, cancelled)
- Count per status
- Percentage breakdown

**Use Case**: Monitor attendance rates and no-shows

### Generating Reports

#### One-Time Report
1. Go to report detail page
2. Click **Generate Report**
3. View the data on screen

#### Export Report
1. Go to report detail page
2. Click **Export**
3. Choose format:
   - **CSV**: Simple, opens in Excel/Google Sheets
   - **Excel**: Professional formatting, styled headers
   - **PDF**: Print-ready, professional layout
4. Download the file

**Direct Export URL:**
```
/business/reports/1/export/?format=csv
/business/reports/1/export/?format=xlsx
/business/reports/1/export/?format=pdf
```

### Export Format Comparison

| Feature | CSV | Excel | PDF |
|---------|-----|-------|-----|
| File Size | Small | Medium | Large |
| Formatting | Basic | Professional | Professional |
| Editable | Yes | Yes | No |
| Print-Ready | No | Yes | Yes |
| Charts | No | Manual | No |
| Best For | Data analysis | Presentations | Printing |

### Scheduled Reports (Coming Soon)

Set up automated reports:
1. Enable **Scheduled** when creating report
2. Choose **Frequency**: Daily, Weekly, Monthly
3. Reports will be generated automatically
4. Receive email notifications (future feature)

### Report Best Practices

✅ **Name Reports Clearly**: Include event name and date range
✅ **Use Filters**: Focus on specific data (e.g., only confirmed registrations)
✅ **Choose Right Format**: 
   - CSV for data analysis
   - Excel for presentations
   - PDF for printing/archiving
✅ **Schedule Regular Reports**: Weekly revenue reports, daily registration updates
✅ **Export Before Events**: Have attendance lists ready for check-in

---

## 🎯 Common Workflows

### Workflow 1: Event Planning
1. Create event in Events module
2. Create tasks for all major activities:
   - Book venue (High priority)
   - Arrange catering (Medium priority)
   - Send invitations (High priority)
   - Set up registration (Urgent)
3. Assign tasks to team members
4. Track progress daily
5. Export task list weekly for team meetings

### Workflow 2: Pre-Event Preparation
1. Filter tasks by event and status "In Progress"
2. Check overdue tasks (shown in red)
3. Update progress percentages
4. Generate Registration Report (Excel format)
5. Review attendee list
6. Export Attendance Report for check-in staff

### Workflow 3: Post-Event Analysis
1. Mark all tasks as completed
2. Log actual hours spent
3. Generate Revenue Report (PDF)
4. Generate Attendance Report (Excel)
5. Export all reports for stakeholders
6. Archive reports for future reference

### Workflow 4: Weekly Team Meeting
1. Export tasks to CSV
2. Filter by "In Progress" and "Overdue"
3. Review with team
4. Update priorities and due dates
5. Assign new tasks
6. Generate Revenue Report to track ticket sales

---

## 🔧 Troubleshooting

### Task Issues

**Q: I can't see tasks for my event**
- Make sure you're logged in as the event organizer
- Check that the event is selected in the filter dropdown

**Q: Can't assign task to team member**
- Ensure the team member is added to the event team
- Check that the team member is marked as "Active"

**Q: Export button not working**
- Check your browser's download settings
- Try a different browser
- Contact support if issue persists

### Report Issues

**Q: Excel export shows error**
- Ensure `openpyxl` is installed: `pip install openpyxl`
- Contact your system administrator

**Q: PDF export shows error**
- Ensure `reportlab` is installed: `pip install reportlab`
- Contact your system administrator

**Q: Report shows no data**
- Check that your event has registrations
- Verify the filters are not too restrictive
- Try generating without filters first

**Q: Export file won't open**
- Check file extension matches format (.csv, .xlsx, .pdf)
- Try opening with different application
- Re-download the file

---

## 📞 Support

### Getting Help
- **Documentation**: Check TECHNICAL_DOCUMENTATION.md
- **Email**: support@eventmanagement.com
- **Phone**: 1-800-EVENT-HELP

### Feature Requests
Have ideas for improvements? Contact us with:
- What you want to do
- Why it would be helpful
- How you currently work around it

---

## 🎓 Training Resources

### Video Tutorials (Coming Soon)
- Creating and managing tasks
- Generating reports
- Bulk task operations
- Advanced filtering

### Webinars
- Monthly organizer training sessions
- Q&A with product team
- Best practices sharing

---

## 📝 Quick Reference

### Task Keyboard Shortcuts
- `Ctrl + N`: New task (when on task list)
- `Ctrl + S`: Save task (when editing)
- `Ctrl + F`: Search tasks

### Task Status Colors
- 🔵 **To Do**: Secondary (gray)
- 🟢 **In Progress**: Primary (blue)
- 🟡 **Review**: Info (light blue)
- ✅ **Completed**: Success (green)
- 🔴 **Cancelled**: Danger (red)

### Task Priority Colors
- 🟢 **Low**: Secondary (gray)
- 🔵 **Medium**: Info (blue)
- 🟡 **High**: Warning (yellow)
- 🔴 **Urgent**: Danger (red)

### Report URLs
- List: `/business/reports/`
- Create: `/business/reports/create/`
- Export: `/business/reports/{id}/export/?format={csv|xlsx|pdf}`

### Task URLs
- List: `/advanced/tasks/`
- Create: `/advanced/tasks/create/`
- Export: `/advanced/tasks/export/`
- Bulk Update: `/advanced/tasks/bulk-update/`

---

*Last Updated: January 2026*
*Version: 1.0*
