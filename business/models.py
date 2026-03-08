from django.db import models
from django.conf import settings
from django.utils import timezone
from events.models import Event
import uuid

User = settings.AUTH_USER_MODEL


# ============ Sponsor Management ============

class SponsorTier(models.TextChoices):
    PLATINUM = 'platinum', 'Platinum'
    GOLD = 'gold', 'Gold'
    SILVER = 'silver', 'Silver'
    BRONZE = 'bronze', 'Bronze'
    STARTUP = 'startup', 'Startup'
    MEDIA = 'media', 'Media Partner'


class BusinessSponsor(models.Model):
    """Sponsor companies for events (Business Module)"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='business_sponsors')
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    tier = models.CharField(max_length=20, choices=SponsorTier.choices, default=SponsorTier.BRONZE)
    
    # Company info
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='sponsor_logos/', blank=True, null=True)
    
    # Booth/Location
    booth_number = models.CharField(max_length=50, blank=True)
    booth_location = models.TextField(blank=True)
    booth_size = models.CharField(max_length=50, blank=True)
    
    # Package details
    package_details = models.JSONField(default=dict, blank=True)
    benefits = models.TextField(blank=True)
    
    # Payment
    sponsorship_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('partial', 'Partial'),
            ('paid', 'Paid'),
            ('waived', 'Waived'),
        ],
        default='pending'
    )
    payment_notes = models.TextField(blank=True)
    
    # Status
    is_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['tier', 'company_name']
    
    def __str__(self):
        return f"{self.company_name} ({self.get_tier_display()})"


class SponsorBenefit(models.Model):
    """Benefits included in sponsor tiers"""
    tier = models.CharField(max_length=20, choices=SponsorTier.choices)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_included = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['tier']
    
    def __str__(self):
        return f"{self.get_tier_display()} - {self.name}"


class SponsorMaterial(models.Model):
    """Marketing materials from sponsors"""
    sponsor = models.ForeignKey(BusinessSponsor, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='sponsor_materials/')
    file_type = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sponsor.company_name} - {self.title}"


class SponsorLead(models.Model):
    """Leads collected by sponsors at the event"""
    sponsor = models.ForeignKey(BusinessSponsor, on_delete=models.CASCADE, related_name='leads')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sponsor_leads')
    
    # Lead info
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    
    # Interest
    interests = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    
    # Source
    source = models.CharField(max_length=100, blank=True)
    scanned_qr = models.BooleanField(default=False)
    
    # Follow-up status
    follow_up_status = models.CharField(
        max_length=20,
        choices=[
            ('new', 'New'),
            ('contacted', 'Contacted'),
            ('qualified', 'Qualified'),
            ('converted', 'Converted'),
            ('lost', 'Lost'),
        ],
        default='new'
    )
    follow_up_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.sponsor.company_name}"


# ============ Analytics ============

class EventAnalytics(models.Model):
    """Analytics data for events"""
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='business_analytics')
    
    # Registration stats
    total_registrations = models.IntegerField(default=0)
    confirmed_registrations = models.IntegerField(default=0)
    cancelled_registrations = models.IntegerField(default=0)
    checked_in_count = models.IntegerField(default=0)
    
    # Revenue stats
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Ticket breakdown
    tickets_by_type = models.JSONField(default=dict, blank=True)
    
    # Traffic stats
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    
    # Engagement
    avg_session_duration = models.IntegerField(default=0)  # in seconds
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Daily breakdown (JSON for flexibility)
    daily_registrations = models.JSONField(default=list, blank=True)
    daily_revenue = models.JSONField(default=list, blank=True)
    
    # Last updated
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics: {self.event.title}"
    
    def update_stats(self):
        """Update analytics from event data"""
        from registration.models import Registration, RegistrationStatus
        
        registrations = Registration.objects.filter(event=self.event)
        
        self.total_registrations = registrations.count()
        self.confirmed_registrations = registrations.filter(status=RegistrationStatus.CONFIRMED).count()
        self.cancelled_registrations = registrations.filter(status__in=[RegistrationStatus.CANCELLED, RegistrationStatus.REFUNDED]).count()
        self.checked_in_count = registrations.filter(status=RegistrationStatus.CHECKED_IN).count()
        
        self.total_revenue = sum(r.total_amount for r in registrations)
        self.total_refunds = sum(r.refund_amount for r in registrations)
        self.net_revenue = self.total_revenue - self.total_refunds
        
        self.save()


class SessionAnalytics(models.Model):
    """Analytics for individual sessions"""
    session = models.OneToOneField('events.EventSession', on_delete=models.CASCADE, related_name='analytics')
    
    # Attendance
    registered_count = models.IntegerField(default=0)
    attended_count = models.IntegerField(default=0)
    avg_duration = models.IntegerField(default=0)  # in minutes
    
    # Ratings
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_ratings = models.IntegerField(default=0)
    
    # Engagement
    questions_asked = models.IntegerField(default=0)
    poll_responses = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics: {self.session.title}"


# ============ Financial Tools ============

class ExpenseCategory(models.TextChoices):
    VENUE = 'venue', 'Venue'
    CATERING = 'catering', 'Catering'
    MARKETING = 'marketing', 'Marketing'
    SPEAKER = 'speaker', 'Speaker Fees'
    STAFF = 'staff', 'Staff'
    EQUIPMENT = 'equipment', 'Equipment'
    TRAVEL = 'travel', 'Travel'
    PRINTING = 'printing', 'Printing'
    SOFTWARE = 'software', 'Software'
    OTHER = 'other', 'Other'


class Expense(models.Model):
    """Event expenses"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices)
    
    description = models.CharField(max_length=255)
    vendor = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dates
    expense_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    
    # Payment
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('paid', 'Paid'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Receipt
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['expense_date']
    
    def __str__(self):
        return f"{self.description} - ${self.amount}"


class Budget(models.Model):
    """Event budget planning"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices)
    
    planned_amount = models.DecimalField(max_digits=10, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['event', 'category']
    
    def __str__(self):
        return f"{self.event.title} - {self.get_category_display()}"
    
    @property
    def variance(self):
        return self.planned_amount - self.actual_amount
    
    @property
    def variance_percent(self):
        if self.planned_amount > 0:
            return ((self.planned_amount - self.actual_amount) / self.planned_amount) * 100
        return 0


class Invoice(models.Model):
    """Invoices for sponsors or clients"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    
    # Client info
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField()
    client_address = models.TextField(blank=True)
    
    # Invoice details
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # PDF
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        self.tax_amount = self.amount * (self.tax_rate / 100)
        self.total_amount = self.amount + self.tax_amount
        super().save(*args, **kwargs)


class Quote(models.Model):
    """Quotes for potential clients"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='quotes', null=True, blank=True)
    quote_number = models.CharField(max_length=50, unique=True)
    
    # Client info
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField()
    client_company = models.CharField(max_length=255, blank=True)
    
    # Quote details
    items = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Validity
    valid_until = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Quote {self.quote_number}"
    
    def save(self, *args, **kwargs):
        if not self.quote_number:
            self.quote_number = f"QT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


# ============ Reporting ============

class Report(models.Model):
    """Saved reports"""
    REPORT_TYPES = [
        ('registration', 'Registration Report'),
        ('revenue', 'Revenue Report'),
        ('attendance', 'Attendance Report'),
        ('engagement', 'Engagement Report'),
        ('sponsor', 'Sponsor Report'),
        ('expense', 'Expense Report'),
        ('custom', 'Custom Report'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reports')
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    # Report configuration
    filters = models.JSONField(default=dict, blank=True)
    columns = models.JSONField(default=list, blank=True)
    
    # Schedule
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class ReportExport(models.Model):
    """Exported reports"""
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='exports')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    file = models.FileField(upload_to='reports/')
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.report.name} - {self.format.upper()}"