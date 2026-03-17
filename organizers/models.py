from django.db import models
from django.conf import settings
from events.models import Event

User = settings.AUTH_USER_MODEL


class OrganizerProfile(models.Model):
    """Organizer profile with company/organization details"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organizer_profile')
    company_name = models.CharField(max_length=255)
    company_description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organizer_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Social links
    facebook_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_documents = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    
    # Subscription
    subscription_plan = models.CharField(max_length=50, default='free')
    subscription_expires = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.company_name


class OrganizerTeamMember(models.Model):
    """Team members for organizer accounts with multi-event support"""
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='team_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=100)
    permissions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    # Multi-event assignment
    events = models.ManyToManyField(Event, related_name='organizer_team_members', blank=True)
    
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.role}"
    
    def get_assigned_events(self):
        """Return all events this team member is assigned to"""
        return self.events.all()
    
    def assign_to_event(self, event):
        """Assign team member to an event"""
        self.events.add(event)
    
    def remove_from_event(self, event):
        """Remove team member from an event"""
        self.events.remove(event)


class EventAnalytics(models.Model):
    """Analytics data for events"""
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='analytics')
    
    # Views and engagement
    total_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    
    # Registrations
    total_registrations = models.IntegerField(default=0)
    confirmed_registrations = models.IntegerField(default=0)
    cancelled_registrations = models.IntegerField(default=0)
    checked_in_count = models.IntegerField(default=0)
    
    # Revenue
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Ticket breakdown
    tickets_sold_by_type = models.JSONField(default=dict)
    
    # Traffic sources
    traffic_sources = models.JSONField(default=dict)
    
    # Daily stats (stored as JSON for simplicity)
    daily_stats = models.JSONField(default=dict)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.event.title}"


class EventTemplate(models.Model):
    """Reusable event templates"""
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Template content
    event_type = models.CharField(max_length=50, blank=True)
    default_description = models.TextField(blank=True)
    session_template = models.JSONField(default=list)
    
    # Branding defaults
    default_primary_color = models.CharField(max_length=7, default='#007bff')
    default_secondary_color = models.CharField(max_length=7, default='#6c757d')
    
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class OrganizerNotification(models.Model):
    """Notifications for organizers"""
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class OrganizerPayout(models.Model):
    """Payout records for organizers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment details
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payout {self.id} - {self.amount}"
