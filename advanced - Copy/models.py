from django.db import models
from django.conf import settings
from django.utils import timezone
from events.models import Event
import uuid

User = settings.AUTH_USER_MODEL


# ============ Vendor Management ============

class VendorCategory(models.TextChoices):
    CATERING = 'catering', 'Catering'
    AV_EQUIPMENT = 'av_equipment', 'Audio/Visual Equipment'
    DECORATION = 'decoration', 'Decoration & Florals'
    PHOTOGRAPHY = 'photography', 'Photography & Video'
    TRANSPORTATION = 'transportation', 'Transportation'
    SECURITY = 'security', 'Security'
    VENUE = 'venue', 'Venue'
    ENTERTAINMENT = 'entertainment', 'Entertainment'
    PRINTING = 'printing', 'Printing Services'
    OTHER = 'other', 'Other'


class Vendor(models.Model):
    """Vendor contacts for events"""
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=VendorCategory.choices)
    
    # Contact info
    contact_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Company info
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    
    # Pricing
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    flat_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Rating
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.IntegerField(default=0)
    
    # Status
    is_preferred = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_preferred', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class VendorContact(models.Model):
    """Contact history with vendors"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='contacts')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    
    contact_date = models.DateTimeField(default=timezone.now)
    contact_type = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('meeting', 'Meeting'),
            ('site_visit', 'Site Visit'),
        ]
    )
    notes = models.TextField()
    follow_up_date = models.DateField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.vendor.name} - {self.contact_date}"


class Contract(models.Model):
    """Contracts with vendors"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='contracts')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='vendor_contracts')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Financials
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_terms = models.TextField(blank=True)
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Files
    contract_file = models.FileField(upload_to='contracts/', blank=True, null=True)
    signed_file = models.FileField(upload_to='contracts/signed/', blank=True, null=True)
    
    # Signatures
    signed_by_vendor = models.BooleanField(default=False)
    signed_by_client = models.BooleanField(default=False)
    vendor_signature_date = models.DateField(null=True, blank=True)
    client_signature_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.vendor.name}"


class VendorPayment(models.Model):
    """Payments to vendors"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payments')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    invoice_number = models.CharField(max_length=50, blank=True)
    receipt = models.FileField(upload_to='vendor_payments/', blank=True, null=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment to {self.vendor.name} - ${self.amount}"


# ============ Team Collaboration ============

class TeamRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    ORGANIZER = 'organizer', 'Organizer'
    COORDINATOR = 'coordinator', 'Coordinator'
    VOLUNTEER = 'volunteer', 'Volunteer'
    SPEAKER_LIAISON = 'speaker_liaison', 'Speaker Liaison'
    SPONSOR_LIAISON = 'sponsor_liaison', 'Sponsor Liaison'
    REGISTRATION_STAFF = 'registration_staff', 'Registration Staff'
    TECHNICAL_SUPPORT = 'technical_support', 'Technical Support'


class UsherAssignment(models.Model):
    """Usher assignments to specific event venues with login credentials"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usher_assignments')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='usher_assignments')
    
    # Venue name (from event's venue_name field)
    venue_name = models.CharField(max_length=255, blank=True, default='')
    
    # Auto-generated credentials
    temp_password = models.CharField(max_length=128)
    password_set_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'event', 'venue_name']
    
    def __str__(self):
        return f"{self.user.email} - {self.event.title} ({self.venue_name})"


class TeamMember(models.Model):
    """Team members for events"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='advanced_team_memberships')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='team_members')
    
    role = models.CharField(max_length=30, choices=TeamRole.choices)
    department = models.CharField(max_length=100, blank=True)
    
    # Permissions
    can_manage_registrations = models.BooleanField(default=False)
    can_manage_sessions = models.BooleanField(default=False)
    can_manage_sponsors = models.BooleanField(default=False)
    can_view_financials = models.BooleanField(default=False)
    can_manage_team = models.BooleanField(default=False)
    
    # Schedule
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'event']
    
    def __str__(self):
        return f"{self.user.email} - {self.event.title} ({self.get_role_display()})"


class Task(models.Model):
    """Tasks for team members"""
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        TeamMember, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tasks'
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Progress tracking
    progress_percentage = models.IntegerField(default=0, help_text='0-100')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Due date
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Dependencies
    depends_on = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dependents'
    )
    
    # Tags for categorization
    tags = models.CharField(max_length=255, blank=True, help_text='Comma-separated tags')
    
    # Attachments
    attachment = models.FileField(upload_to='task_attachments/', blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'due_date', 'created_at']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return self.title
    
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False
    
    def get_priority_color(self):
        """Get color for priority badge"""
        colors = {
            'low': 'secondary',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger'
        }
        return colors.get(self.priority, 'secondary')
    
    def get_status_color(self):
        """Get color for status badge"""
        colors = {
            'todo': 'secondary',
            'in_progress': 'primary',
            'review': 'info',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return colors.get(self.status, 'secondary')
    
    def can_start(self):
        """Check if task can be started (dependencies met)"""
        if self.depends_on:
            return self.depends_on.status == 'completed'
        return True
    
    def mark_completed(self):
        """Mark task as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()


class TaskComment(models.Model):
    """Comments on tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_comments')
    
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.task.title}"


class TeamNotification(models.Model):
    """Notifications for team members"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_notifications')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('task', 'Task Assigned'),
            ('update', 'Event Update'),
            ('deadline', 'Deadline Reminder'),
            ('announcement', 'Announcement'),
        ]
    )
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


# ============ Security & Compliance ============

class AuditLog(models.Model):
    """Audit log for tracking changes"""
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('view', 'Viewed'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Exported'),
        ('check_in', 'Check-in'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    content_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    
    # Details
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Snapshot of changed data
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.content_type} at {self.created_at}"


class DataExport(models.Model):
    """Track data exports for GDPR compliance"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_exports')
    
    export_type = models.CharField(max_length=50)
    formats = models.JSONField(default=list)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # File
    file = models.FileField(upload_to='data_exports/', blank=True, null=True)
    error_message = models.TextField(blank=True)
    
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"Export by {self.user.email} - {self.export_type}"


class PrivacySetting(models.Model):
    """User privacy settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy_settings')
    
    # Data sharing
    share_with_sponsors = models.BooleanField(default=False)
    share_with_speakers = models.BooleanField(default=False)
    
    # Communications
    marketing_emails = models.BooleanField(default=True)
    event_updates = models.BooleanField(default=True)
    
    # Data retention
    retain_registration_history = models.BooleanField(default=True)
    retain_session_attendance = models.BooleanField(default=True)
    
    # Analytics
    allow_analytics = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Privacy settings for {self.user.email}"


class SecurityEvent(models.Model):
    """Security-related events"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    EVENT_TYPES = [
        ('failed_login', 'Failed Login Attempt'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('data_breach', 'Data Breach Attempt'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('policy_violation', 'Policy Violation'),
    ]
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='low')
    
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='resolved_security_events'
    )
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.created_at}"