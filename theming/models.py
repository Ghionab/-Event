from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from events.models import Event
import hashlib
import json

User = get_user_model()


class EventTheme(models.Model):
    """Main theme model for events"""
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='theme')
    
    # Color Palette
    primary_color = models.CharField(max_length=7, help_text="Hex color code")
    secondary_color = models.CharField(max_length=7, help_text="Hex color code")
    accent_color = models.CharField(max_length=7, help_text="Hex color code")
    neutral_light = models.CharField(max_length=7, help_text="Hex color code")
    neutral_dark = models.CharField(max_length=7, help_text="Hex color code")
    
    # Generated CSS
    css_content = models.TextField(help_text="Generated CSS theme content")
    css_hash = models.CharField(max_length=64, unique=True, help_text="SHA-256 hash for caching")
    
    # Metadata
    extraction_confidence = models.FloatField(default=0.0, help_text="Confidence score 0-1")
    is_fallback = models.BooleanField(default=False, help_text="Whether fallback theme was used")
    
    GENERATION_METHODS = [
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
        ('fallback', 'Fallback'),
    ]
    generation_method = models.CharField(max_length=50, choices=GENERATION_METHODS, default='auto')
    
    # Accessibility
    wcag_compliant = models.BooleanField(default=True, help_text="WCAG 2.1 AA compliant")
    contrast_adjustments_made = models.BooleanField(default=False, help_text="Colors adjusted for accessibility")
    
    # Performance
    cache_key = models.CharField(max_length=100, unique=True, help_text="Unique cache identifier")
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['css_hash']),
            models.Index(fields=['cache_key']),
            models.Index(fields=['last_accessed']),
        ]
        verbose_name = "Event Theme"
        verbose_name_plural = "Event Themes"
    
    def __str__(self):
        return f"Theme for {self.event.title}"
    
    def save(self, *args, **kwargs):
        # Generate CSS hash if CSS content exists
        if self.css_content:
            self.css_hash = hashlib.sha256(self.css_content.encode()).hexdigest()
        
        # Generate cache key if not exists
        if not self.cache_key:
            self.cache_key = f"theme_{self.event.id}_{timezone.now().timestamp()}"
        
        super().save(*args, **kwargs)
    
    def increment_access_count(self):
        """Increment access count for analytics"""
        self.access_count += 1
        self.save(update_fields=['access_count', 'last_accessed'])


class ColorPalette(models.Model):
    """Extracted color palette from brand assets"""
    theme = models.OneToOneField(EventTheme, on_delete=models.CASCADE, related_name='palette')
    
    # Extracted Colors (JSON field for flexibility)
    extracted_colors = models.JSONField(
        default=list, 
        help_text="List of extracted colors with confidence and frequency data"
    )
    
    # Source Information
    source_image = models.CharField(max_length=255, help_text="Path to source image")
    
    EXTRACTION_ALGORITHMS = [
        ('kmeans', 'K-Means Clustering'),
        ('colorthief', 'Color Thief'),
        ('dominant', 'Dominant Color'),
        ('manual', 'Manual Selection'),
    ]
    extraction_algorithm = models.CharField(
        max_length=50, 
        choices=EXTRACTION_ALGORITHMS, 
        default='kmeans'
    )
    extraction_parameters = models.JSONField(default=dict, help_text="Algorithm parameters used")
    
    # Quality Metrics
    color_diversity_score = models.FloatField(default=0.0, help_text="Color diversity score 0-1")
    overall_confidence = models.FloatField(default=0.0, help_text="Overall extraction confidence 0-1")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Color Palette"
        verbose_name_plural = "Color Palettes"
    
    def __str__(self):
        return f"Palette for {self.theme.event.title}"
    
    def get_primary_colors(self, count=3):
        """Get the top N primary colors by confidence"""
        if not self.extracted_colors:
            return []
        
        # Sort by confidence score
        sorted_colors = sorted(
            self.extracted_colors, 
            key=lambda x: x.get('confidence', 0), 
            reverse=True
        )
        return sorted_colors[:count]
    
    def get_color_by_frequency(self, count=3):
        """Get the top N colors by frequency in image"""
        if not self.extracted_colors:
            return []
        
        # Sort by frequency
        sorted_colors = sorted(
            self.extracted_colors, 
            key=lambda x: x.get('frequency', 0), 
            reverse=True
        )
        return sorted_colors[:count]


class ThemeVariation(models.Model):
    """Different variations of a theme (light/dark, different intensities)"""
    base_theme = models.ForeignKey(EventTheme, on_delete=models.CASCADE, related_name='variations')
    
    VARIATION_TYPES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
        ('high_contrast', 'High Contrast'),
        ('colorblind_friendly', 'Colorblind Friendly'),
        ('minimal', 'Minimal'),
        ('vibrant', 'Vibrant'),
    ]
    variation_type = models.CharField(max_length=50, choices=VARIATION_TYPES)
    css_content = models.TextField(help_text="CSS content for this variation")
    css_hash = models.CharField(max_length=64, help_text="SHA-256 hash for caching")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['base_theme', 'variation_type']
        verbose_name = "Theme Variation"
        verbose_name_plural = "Theme Variations"
    
    def __str__(self):
        return f"{self.base_theme.event.title} - {self.get_variation_type_display()}"
    
    def save(self, *args, **kwargs):
        # Generate CSS hash
        if self.css_content:
            self.css_hash = hashlib.sha256(self.css_content.encode()).hexdigest()
        super().save(*args, **kwargs)


class ThemeCache(models.Model):
    """Cache table for theme performance optimization"""
    cache_key = models.CharField(max_length=100, unique=True, primary_key=True)
    theme = models.ForeignKey(EventTheme, on_delete=models.CASCADE, related_name='cache_entries')
    
    # Cached Content
    css_content = models.TextField(help_text="Cached CSS content")
    
    PORTAL_TYPES = [
        ('staff', 'Staff Portal'),
        ('participant', 'Participant Portal'),
        ('organizer', 'Organizer Portal'),
        ('universal', 'Universal'),
    ]
    portal_type = models.CharField(max_length=20, choices=PORTAL_TYPES)
    
    # Cache Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    expires_at = models.DateTimeField(help_text="Cache expiration time")
    
    class Meta:
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['last_accessed']),
            models.Index(fields=['portal_type']),
        ]
        verbose_name = "Theme Cache"
        verbose_name_plural = "Theme Cache Entries"
    
    def __str__(self):
        return f"Cache: {self.theme.event.title} ({self.get_portal_type_display()})"
    
    def is_expired(self):
        """Check if cache entry is expired"""
        return timezone.now() > self.expires_at
    
    def increment_access_count(self):
        """Increment access count for analytics"""
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])


class ThemeGenerationLog(models.Model):
    """Audit log for theme generation activities"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='theme_logs')
    
    # Operation Details
    OPERATION_TYPES = [
        ('generation', 'Theme Generation'),
        ('fallback', 'Fallback Applied'),
        ('manual_override', 'Manual Override'),
        ('cache_hit', 'Cache Hit'),
        ('cache_miss', 'Cache Miss'),
        ('accessibility_fix', 'Accessibility Fix'),
        ('variation_created', 'Variation Created'),
    ]
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPES)
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('partial', 'Partial Success'),
        ('warning', 'Warning'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Processing Information
    processing_time_ms = models.IntegerField(null=True, blank=True, help_text="Processing time in milliseconds")
    error_message = models.TextField(blank=True, help_text="Error details if operation failed")
    extraction_confidence = models.FloatField(null=True, blank=True, help_text="Color extraction confidence")
    
    # Source Information
    source_image_path = models.CharField(max_length=255, blank=True, help_text="Path to source image")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="User who triggered the operation")
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional operation metadata")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['operation_type']),
        ]
        ordering = ['-created_at']
        verbose_name = "Theme Generation Log"
        verbose_name_plural = "Theme Generation Logs"
    
    def __str__(self):
        return f"{self.event.title} - {self.get_operation_type_display()} ({self.get_status_display()})"
    
    @classmethod
    def log_operation(cls, event, operation_type, status, **kwargs):
        """Convenience method to create log entries"""
        return cls.objects.create(
            event=event,
            operation_type=operation_type,
            status=status,
            **kwargs
        )


# Extend the existing Event model with theme-related fields
def extend_event_model():
    """
    This function would be called to add theme-related fields to the existing Event model.
    Since we can't modify the existing model directly, we'll document the required fields here.
    
    Required additions to Event model:
    - brand_assets = models.JSONField(default=list)  # Multiple brand images
    - theme_preferences = models.JSONField(default=dict)  # User preferences
    - auto_theming_enabled = models.BooleanField(default=True)
    - theme_generation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    - theme_last_updated = models.DateTimeField(null=True, blank=True)
    """
    pass