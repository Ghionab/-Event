from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for the custom User model"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    ORGANIZER = 'organizer', 'Event Organizer'
    STAFF = 'staff', 'Gate Staff'
    USHER = 'usher', 'Usher'
    COORDINATOR = 'coordinator', 'Coordinator'
    SPEAKER = 'speaker', 'Speaker'
    SPONSOR = 'sponsor', 'Sponsor'
    ATTENDEE = 'attendee', 'Attendee'


class User(AbstractUser):
    """Custom User model with email as primary identifier"""
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.ATTENDEE
    )
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    is_verified = models.BooleanField(default=False)
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.email
    
    @property
    def is_organizer(self):
        """Check if user is an organizer"""
        return self.role == UserRole.ORGANIZER or hasattr(self, 'organizer_profile')
