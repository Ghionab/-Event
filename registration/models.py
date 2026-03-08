from django.db import models
from django.conf import settings
from django.utils import timezone
from events.models import Event
import uuid

User = settings.AUTH_USER_MODEL


class TicketCategory(models.TextChoices):
    FREE = 'free', 'Free'
    EARLY_BIRD = 'early_bird', 'Early Bird'
    REGULAR = 'regular', 'Regular'
    VIP = 'vip', 'VIP'
    STUDENT = 'student', 'Student'


class RegistrationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELLED = 'cancelled', 'Cancelled'
    WAITLISTED = 'waitlisted', 'Waitlisted'
    CHECKED_IN = 'checked_in', 'Checked In'
    REFUNDED = 'refunded', 'Refunded'


class TicketType(models.Model):
    """Ticket types for events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ticket_category = models.CharField(
        max_length=20,
        choices=TicketCategory.choices,
        default=TicketCategory.REGULAR
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_available = models.IntegerField()
    quantity_sold = models.IntegerField(default=0)
    
    # Sales window
    sales_start = models.DateTimeField()
    sales_end = models.DateTimeField()
    
    # Benefits/perks
    benefits = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.event.title} - {self.name}"
    
    @property
    def available_quantity(self):
        return self.quantity_available - self.quantity_sold
    
    @property
    def is_sold_out(self):
        return self.quantity_sold >= self.quantity_available
    
    def can_purchase(self):
        now = timezone.now()
        return (
            self.is_active and
            self.sales_start <= now <= self.sales_end and
            not self.is_sold_out
        )


class PromoCode(models.Model):
    """Promotional codes for discounts"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='promo_codes')
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=20,
        choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')],
        default='percentage'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_uses = models.IntegerField(default=0)
    current_uses = models.IntegerField(default=0)
    max_uses_per_user = models.IntegerField(default=1)
    
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.event.title}"
    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.max_uses == 0 or self.current_uses < self.max_uses)
        )
    
    def calculate_discount(self, original_price):
        if self.discount_type == 'percentage':
            return (original_price * self.discount_value) / 100
        else:
            return min(self.discount_value, original_price)
    
    def apply_discount(self, original_price):
        """Returns (discounted_price, discount_amount)"""
        discount = self.calculate_discount(original_price)
        discounted_price = max(0, original_price - discount)
        return (discounted_price, discount)


class Registration(models.Model):
    """Event registration/booking"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations', null=True, blank=True)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.SET_NULL, null=True)
    
    registration_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING
    )
    
    # Payment details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, blank=True
    )
    
    # Attendee info (can be different from user)
    attendee_name = models.CharField(max_length=255)
    attendee_email = models.EmailField()
    attendee_phone = models.CharField(max_length=20, blank=True)
    special_requests = models.TextField(blank=True)
    
    # Custom registration fields (JSON)
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # Check-in
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='registration_checkins'
    )
    
    # Refund details
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_reason = models.TextField(blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # QR Code for check-in
    qr_code = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.attendee_name} - {self.event.title}"
    
    def save(self, *args, **kwargs):
        if not self.registration_number:
            self.registration_number = f"REG-{uuid.uuid4().hex[:8].upper()}"
        if not self.qr_code:
            self.qr_code = str(uuid.uuid4().hex[:16])
        super().save(*args, **kwargs)
    
    def confirm(self):
        """Confirm the registration"""
        if self.status == RegistrationStatus.PENDING:
            self.status = RegistrationStatus.CONFIRMED
            # Update ticket sold count
            if self.ticket_type:
                self.ticket_type.quantity_sold += 1
                self.ticket_type.save()
            self.save()
    
    def cancel(self, reason=''):
        """Cancel the registration"""
        if self.status in [RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED]:
            self.status = RegistrationStatus.CANCELLED
            self.refund_reason = reason
            # Update ticket sold count
            if self.ticket_type and self.status == RegistrationStatus.CONFIRMED:
                self.ticket_type.quantity_sold = max(0, self.ticket_type.quantity_sold - 1)
                self.ticket_type.save()
            self.save()
    
    def refund(self, amount=None, reason=''):
        """Process refund"""
        if self.status == RegistrationStatus.CONFIRMED:
            refund_amount = amount if amount else self.total_amount
            self.status = RegistrationStatus.REFUNDED
            self.refund_amount = refund_amount
            self.refund_reason = reason
            self.refunded_at = timezone.now()
            # Update ticket sold count
            if self.ticket_type:
                self.ticket_type.quantity_sold = max(0, self.ticket_type.quantity_sold - 1)
                self.ticket_type.save()
            self.save()
            return True
        return False
    
    def check_in(self, checked_by=None):
        """Check in the attendee"""
        if self.status == RegistrationStatus.CONFIRMED:
            self.status = RegistrationStatus.CHECKED_IN
            self.checked_in_at = timezone.now()
            self.checked_in_by = checked_by
            self.save()
            return True
        return False

    def generate_qr_code_image(self):
        """Generate QR code image as base64"""
        import qrcode
        from io import BytesIO
        import base64

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    def get_check_in_status(self):
        """Get detailed check-in status"""
        if self.status == RegistrationStatus.CHECKED_IN:
            return {
                'checked_in': True,
                'checked_in_at': self.checked_in_at,
                'checked_in_by': self.checked_in_by,
            }
        return {'checked_in': False}


class RegistrationField(models.Model):
    """Custom registration form fields"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('date', 'Date'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio Buttons'),
        ('file', 'File Upload'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registration_fields')
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    label = models.CharField(max_length=200)
    help_text = models.TextField(blank=True)
    required = models.BooleanField(default=False)
    options = models.TextField(blank=True, help_text='For select/radio/checkbox fields, comma-separated values')
    placeholder = models.CharField(max_length=200, blank=True)
    validation_regex = models.CharField(max_length=200, blank=True)
    min_value = models.CharField(max_length=50, blank=True)
    max_value = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.event.title} - {self.label}"
    
    def get_options_list(self):
        if self.options:
            return [opt.strip() for opt in self.options.split(',')]
        return []

    def get_allowed_file_types(self):
        """Get allowed file extensions for file upload fields"""
        if self.field_type == 'file' and self.options:
            return [opt.strip().lower() for opt in self.options.split(',')]
        # Default allowed file types
        return ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']


class RegistrationDocument(models.Model):
    """Uploaded documents for pre-registration (PDF, Excel, etc.)"""
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE,
        related_name='documents'
    )
    field = models.ForeignKey(
        RegistrationField, on_delete=models.CASCADE,
        related_name='documents'
    )

    # Document details
    file = models.FileField(upload_to='registration_documents/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)  # Stored filename
    file_size = models.IntegerField()  # Size in bytes
    mime_type = models.CharField(max_length=100, blank=True)

    # Validation status
    is_validated = models.BooleanField(default=False)
    validation_notes = models.TextField(blank=True)
    validated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='validated_documents'
    )
    validated_at = models.DateTimeField(null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename} - {self.registration.registration_number}"

    def get_file_extension(self):
        """Get file extension"""
        import os
        return os.path.splitext(self.original_filename)[1].lower()

    def get_file_icon(self):
        """Get icon class based on file type"""
        ext = self.get_file_extension()
        icons = {
            '.pdf': 'fa-file-pdf',
            '.doc': 'fa-file-word',
            '.docx': 'fa-file-word',
            '.xls': 'fa-file-excel',
            '.xlsx': 'fa-file-excel',
            '.csv': 'fa-file-csv',
            '.jpg': 'fa-file-image',
            '.jpeg': 'fa-file-image',
            '.png': 'fa-file-image',
            '.gif': 'fa-file-image',
            '.zip': 'fa-file-archive',
            '.rar': 'fa-file-archive',
        }
        return icons.get(ext, 'fa-file')

    def is_image(self):
        """Check if file is an image"""
        return self.get_file_extension() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    def is_pdf(self):
        """Check if file is PDF"""
        return self.get_file_extension() == '.pdf'

    def is_excel(self):
        """Check if file is Excel"""
        return self.get_file_extension() in ['.xls', '.xlsx', '.csv']


class Waitlist(models.Model):
    """Event waitlist for sold out events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='waitlist')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waitlist_entries')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    position = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=[('waiting', 'Waiting'), ('notified', 'Notified'), ('registered', 'Registered'), ('expired', 'Expired')],
        default='waiting'
    )
    notified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position']
        unique_together = ['event', 'user', 'ticket_type']
    
    def __str__(self):
        return f"{self.user.email} - {self.event.title} (Position {self.position})"


# Phase 4 - Attendee Experience Models

class Badge(models.Model):
    """Event badges for attendees"""
    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name='badge')
    
    # Badge layout
    BADGE_TYPES = [
        ('standard', 'Standard'),
        ('vip', 'VIP'),
        ('speaker', 'Speaker'),
        ('staff', 'Staff'),
        ('sponsor', 'Sponsor'),
        ('vip_speaker', 'VIP Speaker'),
    ]
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, default='standard')
    
    # Badge content
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    
    # Design
    primary_color = models.CharField(max_length=7, default='#007bff')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
    
    # QR Code
    qr_code_data = models.CharField(max_length=255, blank=True)
    
    # Print status
    is_printed = models.BooleanField(default=False)
    printed_at = models.DateTimeField(null=True, blank=True)
    printed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='badges_printed'
    )
    
    # Custom fields
    custom_fields = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['registration__event', 'name']
    
    def __str__(self):
        return f"Badge: {self.name} - {self.registration.event.title}"
    
    def generate_qr_code(self):
        """Generate QR code data"""
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_code_data or f"BADGE:{self.registration.qr_code}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    
    def mark_printed(self, printed_by_user):
        """Mark badge as printed"""
        self.is_printed = True
        self.printed_at = timezone.now()
        self.printed_by = printed_by_user
        self.save()


class CheckIn(models.Model):
    """Check-in log for tracking attendance"""
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='checkins')
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='checkin_records_made')
    
    check_in_time = models.DateTimeField(auto_now_add=True)
    method = models.CharField(
        max_length=20,
        choices=[
            ('qr_scan', 'QR Code Scan'),
            ('manual', 'Manual Entry'),
            ('kiosk', 'Kiosk'),
            ('self', 'Self Check-in'),
        ],
        default='manual'
    )
    
    # Location if applicable
    location = models.CharField(max_length=255, blank=True)
    device_info = models.CharField(max_length=255, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-check_in_time']
    
    def __str__(self):
        return f"{self.registration.attendee_name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"


class AttendeePreference(models.Model):
    """Attendee preferences for event experience"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendee_preferences')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendee_preferences')
    
    # Session preferences
    interested_topics = models.JSONField(default=list, blank=True)
    preferred_tracks = models.JSONField(default=list, blank=True)
    
    # Dietary requirements
    dietary_requirements = models.JSONField(default=list, blank=True)
    dietary_notes = models.TextField(blank=True)
    
    # Accessibility
    accessibility_needs = models.JSONField(default=list, blank=True)
    accessibility_notes = models.TextField(blank=True)
    
    # Networking preferences
    networking_enabled = models.BooleanField(default=True)
    networking_bio = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    
    # Communication preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Session schedule
    saved_sessions = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'event']
    
    def __str__(self):
        return f"Preferences: {self.user.email} - {self.event.title}"


class AttendeeMessage(models.Model):
    """Messages between attendees (networking)"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendee_messages')
    
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related registration (optional)
    registration = models.ForeignKey(
        Registration, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='messages'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.email} to {self.recipient.email}"


class SessionAttendance(models.Model):
    """Track which sessions attendees join"""
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='session_attendance')
    session = models.ForeignKey('events.EventSession', on_delete=models.CASCADE, related_name='attendees')
    
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    # Rating (after session)
    rating = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['registration', 'session']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.registration.attendee_name} - {self.session.title}"


# =============================================================================
# Bulk Registration Models
# =============================================================================

class BulkRegistrationUpload(models.Model):
    """Bulk registration upload from Excel/CSV files"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bulk_uploads')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # File details
    file = models.FileField(upload_to='bulk_registrations/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()

    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Results
    total_rows = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bulk Upload - {self.event.title} - {self.original_filename}"

    def get_status_color(self):
        colors = {
            'pending': 'warning',
            'processing': 'info',
            'completed': 'success',
            'failed': 'danger',
        }
        return colors.get(self.status, 'secondary')


class BulkRegistrationRow(models.Model):
    """Individual row from bulk registration upload"""
    bulk_upload = models.ForeignKey(BulkRegistrationUpload, on_delete=models.CASCADE, related_name='rows')

    # Row data
    row_number = models.IntegerField()
    row_data = models.JSONField(default=dict)  # Original row data

    # Registration link (if created)
    registration = models.OneToOneField(Registration, on_delete=models.SET_NULL, null=True, blank=True)

    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Error details
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['row_number']
        unique_together = ['bulk_upload', 'row_number']

    def __str__(self):
        return f"Row {self.row_number} - {self.status}"


class ManualRegistration(models.Model):
    """Manually created registration by organizer"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='manual_registrations')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='manual_registrations_created')

    # Attendee info
    attendee_name = models.CharField(max_length=255)
    attendee_email = models.EmailField()
    attendee_phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=100, blank=True)

    # Ticket
    ticket_type = models.ForeignKey(TicketType, on_delete=models.SET_NULL, null=True, blank=True)

    # Registration (linked after confirmation)
    registration = models.OneToOneField(Registration, on_delete=models.SET_NULL, null=True, blank=True, related_name='manual_registration')

    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('sent', 'Invitation Sent'),
        ('registered', 'Registered'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Notes
    notes = models.TextField(blank=True)

    # Invite email
    invite_email_sent = models.BooleanField(default=False)
    invite_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.attendee_name} - {self.event.title}"

    def create_registration(self):
        """Create actual registration from manual entry"""
        if self.registration or not self.ticket_type:
            return None

        registration = Registration.objects.create(
            event=self.event,
            attendee_name=self.attendee_name,
            attendee_email=self.attendee_email,
            attendee_phone=self.attendee_phone,
            ticket_type=self.ticket_type,
            total_amount=self.ticket_type.price,
            status=RegistrationStatus.CONFIRMED,
        )

        self.registration = registration
        self.status = 'registered'
        self.save()

        # Update ticket count
        self.ticket_type.quantity_sold += 1
        self.ticket_type.save()

        return registration

    def send_invite(self):
        """Send invitation email to attendee"""
        from django.core.mail import send_mail
        from django.conf import settings

        subject = f"Event Invitation: {self.event.title}"
        message = f"""
Dear {self.attendee_name},

You have been invited to attend {self.event.title}.

Event Details:
- Date: {self.event.start_date.strftime('%B %d, %Y')}
- Venue: {self.event.venue_name or 'TBA'}

Please register using the link below:
http://localhost:8001/events/{self.event.id}/register/

Best regards,
{self.event.organizer.get_full_name() or 'Event Team'}
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.attendee_email],
                fail_silently=False,
            )
            self.invite_email_sent = True
            self.invite_sent_at = timezone.now()
            self.status = 'sent'
            self.save()
            return True
        except Exception:
            return False