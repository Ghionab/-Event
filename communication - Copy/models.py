from django.db import models
from django.conf import settings
from django.utils import timezone
from events.models import Event
import uuid

User = settings.AUTH_USER_MODEL


class EmailTemplate(models.Model):
    """Email templates for automated communications"""
    TEMPLATE_TYPES = [
        ('registration_confirmation', 'Registration Confirmation'),
        ('event_reminder', 'Event Reminder'),
        ('session_reminder', 'Session Reminder'),
        ('check_in_confirmation', 'Check-in Confirmation'),
        ('event_update', 'Event Update'),
        ('event_cancelled', 'Event Cancelled'),
        ('custom', 'Custom Template'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Variables available in template
    available_variables = models.TextField(
        blank=True,
        help_text='Comma-separated list of available variables like {{user_name}}, {{event_title}}, etc.'
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class EmailLog(models.Model):
    """Log of sent emails"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
    ]
    
    recipient = models.EmailField()
    recipient_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='email_logs'
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, null=True, blank=True,
        related_name='email_logs'
    )
    template = models.ForeignKey(
        EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    
    subject = models.CharField(max_length=255)
    content = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    # Error info
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Tracking
    tracking_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Email to {self.recipient} - {self.subject[:50]}"
    
    def mark_sent(self):
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_failed(self, error):
        self.status = 'failed'
        self.error_message = error
        self.retry_count += 1
        self.save()


class ScheduledEmail(models.Model):
    """Scheduled emails to be sent"""
    FREQUENCY_CHOICES = [
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('before_event', 'Before Event'),
        ('before_session', 'Before Session'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='scheduled_emails')
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    
    subject = models.CharField(max_length=255)
    content = models.TextField()
    
    # Recipients
    recipient_filter = models.JSONField(
        default=dict,
        help_text='Filter criteria for recipients (e.g., {"status": "confirmed"})'
    )
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='once')
    scheduled_at = models.DateTimeField()
    last_sent_at = models.DateTimeField(null=True, blank=True)
    next_send_at = models.DateTimeField(null=True, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    max_recipients = models.IntegerField(default=0, help_text='0 = unlimited')
    sent_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_at']
    
    def __str__(self):
        return f"Scheduled: {self.subject} - {self.scheduled_at}"


class SMSNotification(models.Model):
    """SMS notifications for events"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sms_notifications')
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sms_notifications'
    )
    
    phone_number = models.CharField(max_length=20)
    message = models.TextField(max_length=160)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Provider info
    provider = models.CharField(max_length=50, default='twilio')
    provider_message_id = models.CharField(max_length=100, blank=True)
    
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMS to {self.phone_number} - {self.status}"


class PushNotification(models.Model):
    """Push notifications for mobile/web"""
    PLATFORM_CHOICES = [
        ('web', 'Web Push'),
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('all', 'All Platforms'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='push_notifications')
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=200)
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='all')
    target_url = models.URLField(blank=True)
    
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    sent_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Push: {self.title}"


class LivePoll(models.Model):
    """Live polls for sessions"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='live_polls')
    session = models.ForeignKey(
        'events.EventSession', on_delete=models.CASCADE,
        null=True, blank=True, related_name='polls'
    )
    
    question = models.CharField(max_length=255)
    poll_type = models.CharField(
        max_length=20,
        choices=[
            ('single', 'Single Choice'),
            ('multiple', 'Multiple Choice'),
            ('rating', 'Rating Scale'),
            ('wordcloud', 'Word Cloud'),
        ],
        default='single'
    )
    
    options = models.JSONField(
        default=list,
        help_text='List of poll options for single/multiple choice'
    )
    
    is_active = models.BooleanField(default=False)
    show_results_live = models.BooleanField(default=True)
    
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Poll: {self.question[:50]}"


class PollResponse(models.Model):
    """Responses to live polls"""
    poll = models.ForeignKey(LivePoll, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_responses')
    
    # Response data
    selected_options = models.JSONField(default=list)
    rating_value = models.IntegerField(null=True, blank=True)
    wordcloud_response = models.CharField(max_length=100, blank=True)
    
    responded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['poll', 'user']
    
    def __str__(self):
        return f"Response to {self.poll.question[:30]}"


class LiveQA(models.Model):
    """Live Q&A for sessions"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='live_qa')
    session = models.ForeignKey(
        'events.EventSession', on_delete=models.CASCADE,
        null=True, blank=True, related_name='qa_questions'
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qa_questions')
    question = models.TextField()
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_answered = models.BooleanField(default=False)
    answered_at = models.DateTimeField(null=True, blank=True)
    
    # Voting
    upvotes = models.IntegerField(default=0)
    upvoted_by = models.JSONField(default=list, blank=True)
    
    # Answer
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='answered_questions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-upvotes', '-created_at']
    
    def __str__(self):
        return f"Q: {self.question[:50]}"
    
    def upvote(self, user_id):
        if user_id not in self.upvoted_by:
            self.upvoted_by.append(user_id)
            self.upvotes += 1
            self.save()
            return True
        return False


class AutomatedReminder(models.Model):
    """Automated reminder settings for events"""
    REMINDER_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    TRIGGER_CHOICES = [
        ('24_hours', '24 Hours Before'),
        ('1_hour', '1 Hour Before'),
        ('30_minutes', '30 Minutes Before'),
        ('15_minutes', '15 Minutes Before'),
        ('custom', 'Custom Time'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminder_settings')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    custom_hours = models.IntegerField(null=True, blank=True)
    
    message_template = models.TextField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'reminder_type', 'trigger']
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} - {self.get_trigger_display()}"