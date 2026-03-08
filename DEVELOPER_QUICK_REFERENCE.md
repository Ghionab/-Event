# Developer Quick Reference - Tasks & Reports

## Quick Commands

### Run Verification
```bash
python verify_task_report_enhancements.py
```

### Run Migrations
```bash
python manage.py makemigrations advanced business
python manage.py migrate
```

### Install Dependencies
```bash
pip install openpyxl reportlab
```

---

## Task Management API

### Model: `advanced.models.Task`

#### Fields
```python
event = ForeignKey(Event)
title = CharField(max_length=255)
description = TextField()
assigned_to = ForeignKey(TeamMember)
created_by = ForeignKey(User)
status = CharField(choices=STATUS_CHOICES)  # todo, in_progress, review, completed, cancelled
priority = CharField(choices=PRIORITY_CHOICES)  # low, medium, high, urgent
progress_percentage = IntegerField(default=0)  # 0-100
estimated_hours = DecimalField(max_digits=5, decimal_places=2)
actual_hours = DecimalField(max_digits=5, decimal_places=2)
due_date = DateTimeField()
completed_at = DateTimeField()
depends_on = ForeignKey('self')
tags = CharField(max_length=255)  # comma-separated
attachment = FileField(upload_to='task_attachments/')
notes = TextField()
```

#### Methods
```python
task.is_overdue()  # Returns bool
task.get_priority_color()  # Returns 'secondary', 'info', 'warning', 'danger'
task.get_status_color()  # Returns 'secondary', 'primary', 'info', 'success', 'danger'
task.can_start()  # Returns bool (checks dependencies)
task.mark_completed()  # Sets status='completed', completed_at=now(), progress=100
```

#### Usage
```python
from advanced.models import Task
from events.models import Event

# Create task
task = Task.objects.create(
    event=event,
    title='Book venue',
    status='todo',
    priority='high',
    progress_percentage=0,
    estimated_hours=4.0,
    tags='venue,logistics',
    created_by=user
)

# Update progress
task.progress_percentage = 50
task.actual_hours = 2.0
task.save()

# Mark completed
task.mark_completed()

# Check status
if task.is_overdue():
    print(f"Task {task.title} is overdue!")
```

---

## Task Views

### URLs
```python
# List tasks
path('advanced/tasks/', views.task_list, name='task_list')

# Create task
path('advanced/tasks/create/', views.task_create, name='task_create')

# Task detail
path('advanced/tasks/<int:pk>/', views.task_detail, name='task_detail')

# Update task
path('advanced/tasks/<int:pk>/update/', views.task_update, name='task_update')

# Delete task
path('advanced/tasks/<int:pk>/delete/', views.task_delete, name='task_delete')

# Export tasks
path('advanced/tasks/export/', views.task_export, name='task_export')

# Bulk update
path('advanced/tasks/bulk-update/', views.task_bulk_update, name='task_bulk_update')
```

### View Parameters

#### task_list
```python
GET /advanced/tasks/
?event=1              # Filter by event
&status=in_progress   # Filter by status
&priority=high        # Filter by priority
&assigned_to=1        # Filter by team member
&search=venue         # Search title/description/tags
&sort=-created_at     # Sort by field
```

#### task_create
```python
GET /advanced/tasks/create/?event=1  # Pre-select event
```

#### task_export
```python
GET /advanced/tasks/export/
?event=1              # Filter by event
&status=in_progress   # Filter by status
&priority=high        # Filter by priority
```

#### task_bulk_update
```python
POST /advanced/tasks/bulk-update/
{
    'task_ids': [1, 2, 3],
    'action': 'mark_completed'  # or 'change_status', 'change_priority', 'delete'
    'new_status': 'in_progress',  # if action='change_status'
    'new_priority': 'high'  # if action='change_priority'
}
```

---

## Report System API

### Model: `business.models.Report`

#### Fields
```python
event = ForeignKey(Event)
name = CharField(max_length=100)
report_type = CharField(choices=REPORT_TYPES)  # registration, revenue, attendance, etc.
export_format = CharField(choices=EXPORT_FORMATS)  # csv, xlsx, pdf
filters = JSONField(default=dict)
columns = JSONField(default=list)
is_scheduled = BooleanField(default=False)
schedule_frequency = CharField(choices=['daily', 'weekly', 'monthly'])
last_generated = DateTimeField()
next_scheduled = DateTimeField()
report_data = JSONField(default=dict)
created_by = ForeignKey(User)
```

#### Usage
```python
from business.models import Report
from events.models import Event

# Create report
report = Report.objects.create(
    event=event,
    name='Registration Summary',
    report_type='registration',
    export_format='xlsx',
    filters={'status': 'confirmed'},
    created_by=user
)

# Schedule report
report.is_scheduled = True
report.schedule_frequency = 'weekly'
report.save()
```

---

## Report Views

### URLs
```python
# List reports
path('business/reports/', views.report_list, name='report_list')

# Create report
path('business/reports/create/', views.report_create, name='report_create')

# Report detail
path('business/reports/<int:report_id>/', views.report_detail, name='report_detail')

# Generate report
path('business/reports/<int:report_id>/generate/', views.report_generate, name='report_generate')

# Export report
path('business/reports/<int:report_id>/export/', views.report_export, name='report_export')
```

### View Parameters

#### report_export
```python
GET /business/reports/1/export/?format=csv   # CSV export
GET /business/reports/1/export/?format=xlsx  # Excel export
GET /business/reports/1/export/?format=pdf   # PDF export
```

---

## Export Formats

### CSV Export
```python
import csv
from django.http import HttpResponse

response = HttpResponse(content_type='text/csv')
response['Content-Disposition'] = 'attachment; filename="report.csv"'

writer = csv.writer(response)
writer.writerow(['Header1', 'Header2'])
writer.writerow(['Value1', 'Value2'])

return response
```

### Excel Export (requires openpyxl)
```python
import openpyxl
from django.http import HttpResponse
from io import BytesIO

wb = openpyxl.Workbook()
ws = wb.active
ws.append(['Header1', 'Header2'])
ws.append(['Value1', 'Value2'])

output = BytesIO()
wb.save(output)
output.seek(0)

response = HttpResponse(
    output.read(),
    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
response['Content-Disposition'] = 'attachment; filename="report.xlsx"'
return response
```

### PDF Export (requires reportlab)
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table
from django.http import HttpResponse
from io import BytesIO

buffer = BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=letter)

data = [['Header1', 'Header2'], ['Value1', 'Value2']]
table = Table(data)

doc.build([table])
pdf = buffer.getvalue()
buffer.close()

response = HttpResponse(content_type='application/pdf')
response['Content-Disposition'] = 'attachment; filename="report.pdf"'
response.write(pdf)
return response
```

---

## Forms

### TaskForm
```python
from advanced.forms import TaskForm

# Create form with event context
form = TaskForm(event=event, user=request.user)

# Create form with instance
form = TaskForm(instance=task, event=task.event, user=request.user)

# Process form
if form.is_valid():
    task = form.save(commit=False)
    task.created_by = request.user
    task.save()
```

### ReportForm
```python
from business.forms import ReportForm

# Create form
form = ReportForm()

# Process form
if form.is_valid():
    report = form.save(commit=False)
    report.created_by = request.user
    report.save()
```

---

## Permissions

### Task Permissions
```python
from django.contrib.auth.decorators import permission_required

@permission_required('advanced.view_task', raise_exception=True)
def task_list(request):
    pass

@permission_required('advanced.add_task', raise_exception=True)
def task_create(request):
    pass

@permission_required('advanced.change_task', raise_exception=True)
def task_update(request, pk):
    pass

@permission_required('advanced.delete_task', raise_exception=True)
def task_delete(request, pk):
    pass
```

### Report Permissions
```python
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def report_list(request):
    pass
```

---

## Database Queries

### Task Queries
```python
from advanced.models import Task
from events.models import Event

# Get tasks for organizer's events
events = Event.objects.filter(organizer=user)
tasks = Task.objects.filter(event__in=events)

# Get overdue tasks
from django.utils import timezone
overdue_tasks = [t for t in tasks if t.is_overdue()]

# Get tasks by status
todo_tasks = tasks.filter(status='todo')
in_progress_tasks = tasks.filter(status='in_progress')

# Get tasks by priority
urgent_tasks = tasks.filter(priority='urgent')

# Search tasks
search_tasks = tasks.filter(
    Q(title__icontains=query) |
    Q(description__icontains=query) |
    Q(tags__icontains=query)
)

# Get task statistics
stats = {
    'total': tasks.count(),
    'todo': tasks.filter(status='todo').count(),
    'in_progress': tasks.filter(status='in_progress').count(),
    'completed': tasks.filter(status='completed').count(),
    'overdue': sum(1 for t in tasks if t.is_overdue()),
}
```

### Report Queries
```python
from business.models import Report
from registration.models import Registration

# Get reports for event
reports = Report.objects.filter(event=event)

# Get scheduled reports
scheduled_reports = Report.objects.filter(is_scheduled=True)

# Generate registration report data
regs = Registration.objects.filter(event=event)
data = {
    'total': regs.count(),
    'confirmed': regs.filter(status='confirmed').count(),
    'pending': regs.filter(status='pending').count(),
}
```

---

## Testing

### Unit Tests
```python
from django.test import TestCase
from advanced.models import Task
from events.models import Event

class TaskModelTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(title='Test Event')
        self.task = Task.objects.create(
            event=self.event,
            title='Test Task',
            status='todo',
            priority='medium'
        )
    
    def test_is_overdue(self):
        self.assertFalse(self.task.is_overdue())
    
    def test_mark_completed(self):
        self.task.mark_completed()
        self.assertEqual(self.task.status, 'completed')
        self.assertEqual(self.task.progress_percentage, 100)
        self.assertIsNotNone(self.task.completed_at)
```

### Integration Tests
```python
from django.test import TestCase, Client
from django.urls import reverse

class TaskViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass'
        )
        self.client.login(email='test@example.com', password='testpass')
    
    def test_task_list(self):
        response = self.client.get(reverse('advanced:task_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_task_export(self):
        response = self.client.get(reverse('advanced:task_export'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
```

---

## Common Patterns

### Organizer Filtering
```python
# In views
if request.user.is_staff:
    tasks = Task.objects.all()
else:
    events = Event.objects.filter(organizer=request.user)
    tasks = Task.objects.filter(event__in=events)
```

### Event Context in Forms
```python
# In views
def task_create(request):
    event_id = request.GET.get('event')
    event = get_object_or_404(Event, pk=event_id) if event_id else None
    
    form = TaskForm(event=event, user=request.user)
    # ...
```

### Bulk Operations
```python
# In views
task_ids = request.POST.getlist('task_ids')
action = request.POST.get('action')

tasks = Task.objects.filter(id__in=task_ids)

if action == 'mark_completed':
    for task in tasks:
        task.mark_completed()
elif action == 'change_status':
    new_status = request.POST.get('new_status')
    tasks.update(status=new_status)
```

---

## Debugging

### Enable Debug Mode
```python
# settings.py
DEBUG = True
```

### Check Migrations
```bash
python manage.py showmigrations advanced business
```

### Check Model Fields
```python
from advanced.models import Task
print([f.name for f in Task._meta.get_fields()])
```

### Check Permissions
```python
from django.contrib.auth.models import Permission
perms = Permission.objects.filter(content_type__app_label='advanced')
for p in perms:
    print(f"{p.codename}: {p.name}")
```

---

## Performance Tips

1. **Use select_related() for foreign keys**
```python
tasks = Task.objects.select_related('event', 'assigned_to', 'created_by')
```

2. **Use prefetch_related() for reverse foreign keys**
```python
tasks = Task.objects.prefetch_related('comments')
```

3. **Add database indexes**
```python
class Meta:
    indexes = [
        models.Index(fields=['event', 'status']),
        models.Index(fields=['due_date']),
    ]
```

4. **Cache report data**
```python
report.report_data = generated_data
report.save()
```

---

## Troubleshooting

### Import Errors
```bash
# Check if packages are installed
pip list | grep openpyxl
pip list | grep reportlab

# Install if missing
pip install openpyxl reportlab
```

### Migration Errors
```bash
# Reset migrations (development only!)
python manage.py migrate advanced zero
python manage.py migrate business zero
python manage.py migrate

# Or fake migrations
python manage.py migrate --fake advanced
python manage.py migrate --fake business
```

### Permission Errors
```python
# Grant permissions to user
from django.contrib.auth.models import Permission
user.user_permissions.add(
    Permission.objects.get(codename='view_task'),
    Permission.objects.get(codename='add_task'),
)
```

---

*Quick Reference v1.0*
*Last Updated: January 2026*
