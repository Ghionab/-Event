from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class EventType(models.TextChoices):
    IN_PERSON = 'in_person', 'In-Person'
    VIRTUAL = 'virtual', 'Virtual'
    HYBRID = 'hybrid', 'Hybrid'

class EventStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    ONGOING = 'ongoing', 'Ongoing'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

class Event(models.Model):
    """Main Event model for Event Setup Module"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.IN_PERSON
    )
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.PUBLISHED
    )
    
    # Dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    
    # Location (for in-person/hybrid)
    venue_name = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Virtual event details
    virtual_meeting_url = models.URLField(blank=True)
    virtual_platform = models.CharField(max_length=100, blank=True)
    
    # Branding
    logo = models.ImageField(upload_to='event_logos/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#007bff', blank=True)
    secondary_color = models.CharField(max_length=7, default='#6c757d', blank=True)
    
    # Organizer
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    
    # Settings
    max_attendees = models.IntegerField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    require_approval = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Contact info
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def duration(self):
        """Calculate event duration in hours"""
        delta = self.end_date - self.start_date
        return delta.total_seconds() / 3600
    
    @property
    def session_count(self):
        return self.sessions.count()
    
    @property
    def speaker_count(self):
        return self.speakers.count()


class Speaker(models.Model):
    """Speaker profiles for events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='speakers')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='speaker_profiles')
    
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    
    # Profile
    photo = models.ImageField(upload_to='speakers/', blank=True, null=True)
    bio = models.TextField(blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    
    # Social links
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    youtube = models.URLField(blank=True)
    
    # Session assignment
    sessions = models.ManyToManyField('EventSession', related_name='speakers', blank=True)
    
    # Status
    is_confirmed = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Order for display
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_full_social_links(self):
        """Return social links as dict"""
        return {
            'twitter': self.twitter,
            'linkedin': self.linkedin,
            'facebook': self.facebook,
            'instagram': self.instagram,
            'youtube': self.youtube,
        }


class Track(models.Model):
    """Event tracks for organizing sessions"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tracks')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.event.title} - {self.name}"


class EventSession(models.Model):
    """Sessions within an event (Agenda items)"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    
    # Track
    track = models.ForeignKey(Track, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    
    # Capacity
    capacity = models.IntegerField(null=True, blank=True)
    registered_count = models.IntegerField(default=0)
    
    # Session type
    SESSION_TYPES = [
        ('presentation', 'Presentation'),
        ('workshop', 'Workshop'),
        ('panel', 'Panel Discussion'),
        ('networking', 'Networking'),
        ('break', 'Break'),
        ('keynote', 'Keynote'),
        ('breakout', 'Breakout Session'),
        ('other', 'Other'),
    ]
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='presentation')
    
    # Materials
    slides = models.FileField(upload_to='session_slides/', blank=True, null=True)
    recording_url = models.URLField(blank=True)
    resources = models.JSONField(default=list, blank=True)
    
    # Keywords/tags
    tags = models.CharField(max_length=255, blank=True)
    
    # Visibility
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return self.title
    
    @property
    def duration(self):
        """Calculate session duration in minutes"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60
    
    @property
    def is_full(self):
        """Check if session is at capacity"""
        if self.capacity is None:
            return False
        return self.registered_count >= self.capacity
    
    @property
    def available_spots(self):
        """Get number of available spots"""
        if self.capacity is None:
            return None
        return max(0, self.capacity - self.registered_count)
    
    def get_speakers_list(self):
        """Get list of speaker names"""
        return [s.name for s in self.speakers.all()]


class Room(models.Model):
    """Event rooms/venues"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    building = models.CharField(max_length=255, blank=True)
    
    # Virtual room
    virtual_url = models.URLField(blank=True)
    virtual_platform = models.CharField(max_length=100, blank=True)
    
    # Amenities
    amenities = models.JSONField(default=list, blank=True)
    
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Sponsor(models.Model):
    """Event sponsors"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sponsors')
    
    company_name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='sponsors/', blank=True, null=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    
    # Sponsorship tier
    TIER_CHOICES = [
        ('platinum', 'Platinum'),
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('bronze', 'Bronze'),
        ('community', 'Community'),
    ]
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    
    # Contact
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Benefits
    booth_number = models.CharField(max_length=50, blank=True)
    booth_description = models.TextField(blank=True)
    
    # Marketing
    promotional_url = models.URLField(blank=True)
    promotional_video = models.URLField(blank=True)
    
    # Order for display
    display_order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'tier']
    
    def __str__(self):
        return self.company_name
        return f"{self.title} - {self.event.title}"
