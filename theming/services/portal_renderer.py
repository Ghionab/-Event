"""
PortalRenderer service for applying themes consistently across portals.

This module implements theme application across Staff, Participant, and Organizer
portals with Django context processors and template tags.
"""

import logging
from typing import Dict, Any, Optional
from django.template import Context, Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .theme_generator import ThemeGenerator, create_portal_specific_css
from ..models import EventTheme, ThemeCache

logger = logging.getLogger(__name__)


class PortalRenderer:
    """
    Portal theme renderer for consistent theme application across all portals.
    
    Features:
    - Django context processor for theme injection
    - Portal-specific CSS generation (Staff, Participant, Organizer)
    - Template tags for dynamic theme application
    - Theme compatibility validation
    - Caching for performance optimization
    """
    
    PORTAL_TYPES = ['staff', 'participant', 'organizer']
    CACHE_TIMEOUT = 3600  # 1 hour
    
    def __init__(self):
        """Initialize PortalRenderer."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.theme_generator = ThemeGenerator()
    
    def apply_theme(self, portal_type: str, theme: EventTheme, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply theme to specific portal context.
        
        Args:
            portal_type: Type of portal ('staff', 'participant', 'organizer')
            theme: EventTheme instance
            context: Template context dictionary
            
        Returns:
            Enhanced context with theme variables
        """
        try:
            if portal_type not in self.PORTAL_TYPES:
                self.logger.warning(f"Unknown portal type: {portal_type}")
                portal_type = 'participant'  # Default fallback
            
            # Get or generate portal-specific CSS
            portal_css = self.generate_portal_css(theme, portal_type)
            
            # Create theme context
            theme_context = {
                'theme': theme,
                'theme_css': mark_safe(portal_css),
                'theme_colors': {
                    'primary': theme.primary_color,
                    'secondary': theme.secondary_color,
                    'accent': theme.accent_color,
                    'neutral_light': theme.neutral_light,
                    'neutral_dark': theme.neutral_dark,
                },
                'theme_metadata': {
                    'portal_type': portal_type,
                    'generation_method': theme.generation_method,
                    'wcag_compliant': theme.wcag_compliant,
                    'is_fallback': theme.is_fallback,
                    'last_updated': theme.updated_at,
                },
                'theme_variations': self._get_theme_variations(theme),
            }
            
            # Merge with existing context
            enhanced_context = context.copy()
            enhanced_context.update(theme_context)
            
            # Track theme access
            theme.increment_access_count()
            
            return enhanced_context
            
        except Exception as e:
            self.logger.error(f"Failed to apply theme for {portal_type}: {str(e)}")
            # Return context with default theme
            return self._apply_default_theme(context, portal_type)
    
    def generate_portal_css(self, theme: EventTheme, portal_type: str) -> str:
        """
        Generate portal-specific CSS.
        
        Args:
            theme: EventTheme instance
            portal_type: Type of portal
            
        Returns:
            Portal-specific CSS string
        """
        # Check cache first
        cache_key = f"portal_css_{theme.id}_{portal_type}_{theme.updated_at.timestamp()}"
        cached_css = cache.get(cache_key)
        
        if cached_css:
            self.logger.debug(f"Using cached CSS for {portal_type} portal")
            return cached_css
        
        try:
            # Check database cache
            try:
                cache_entry = ThemeCache.objects.get(
                    theme=theme,
                    portal_type=portal_type
                )
                if not cache_entry.is_expired():
                    cache_entry.increment_access_count()
                    # Store in memory cache too
                    cache.set(cache_key, cache_entry.css_content, self.CACHE_TIMEOUT)
                    return cache_entry.css_content
            except ThemeCache.DoesNotExist:
                pass
            
            # Generate new CSS
            base_theme = self.theme_generator.generate_theme({
                'primary_color': theme.primary_color,
                'secondary_color': theme.secondary_color,
                'accent_color': theme.accent_color,
                'neutral_light': theme.neutral_light,
                'neutral_dark': theme.neutral_dark,
            })
            
            portal_css = create_portal_specific_css(base_theme, portal_type)
            
            # Cache in database
            cache_entry, created = ThemeCache.objects.get_or_create(
                cache_key=f"theme_{theme.id}_{portal_type}",
                theme=theme,
                defaults={
                    'css_content': portal_css,
                    'portal_type': portal_type,
                    'expires_at': timezone.now() + timedelta(hours=24)
                }
            )
            
            if not created:
                # Update existing cache
                cache_entry.css_content = portal_css
                cache_entry.expires_at = timezone.now() + timedelta(hours=24)
                cache_entry.save()
            
            # Cache in memory
            cache.set(cache_key, portal_css, self.CACHE_TIMEOUT)
            
            return portal_css
            
        except Exception as e:
            self.logger.error(f"Failed to generate CSS for {portal_type}: {str(e)}")
            return self._get_default_css(portal_type)
    
    def validate_portal_compatibility(self, theme: EventTheme, portal_type: str) -> bool:
        """
        Ensure theme works with portal's UI components.
        
        Args:
            theme: EventTheme instance
            portal_type: Type of portal
            
        Returns:
            True if compatible, False otherwise
        """
        try:
            # Basic validation checks
            if not theme.wcag_compliant:
                self.logger.warning(f"Theme {theme.id} is not WCAG compliant")
                return False
            
            # Check if required colors are present
            required_colors = [
                theme.primary_color,
                theme.secondary_color,
                theme.accent_color,
                theme.neutral_light,
                theme.neutral_dark
            ]
            
            for color in required_colors:
                if not color or not self._is_valid_hex_color(color):
                    self.logger.warning(f"Invalid color in theme {theme.id}: {color}")
                    return False
            
            # Portal-specific validation
            if portal_type == 'staff':
                # Staff portal needs high contrast for scanning operations
                if not self._check_high_contrast(theme.primary_color, theme.neutral_light):
                    self.logger.warning(f"Insufficient contrast for staff portal")
                    return False
            
            elif portal_type == 'participant':
                # Participant portal should be visually appealing
                if theme.is_fallback:
                    self.logger.info(f"Using fallback theme for participant portal")
            
            elif portal_type == 'organizer':
                # Organizer portal needs professional appearance
                if not self._check_professional_colors(theme):
                    self.logger.warning(f"Colors may not be suitable for organizer portal")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Compatibility validation failed: {str(e)}")
            return False
    
    def get_theme_for_event(self, event_id: int) -> Optional[EventTheme]:
        """
        Get theme for specific event.
        
        Args:
            event_id: Event ID
            
        Returns:
            EventTheme instance or None
        """
        try:
            return EventTheme.objects.select_related('event').get(event_id=event_id)
        except EventTheme.DoesNotExist:
            self.logger.warning(f"No theme found for event {event_id}")
            return None
    
    def clear_theme_cache(self, theme: EventTheme, portal_type: Optional[str] = None):
        """
        Clear theme cache for specific theme and portal.
        
        Args:
            theme: EventTheme instance
            portal_type: Optional portal type, clears all if None
        """
        try:
            if portal_type:
                # Clear specific portal cache
                cache_key = f"portal_css_{theme.id}_{portal_type}_{theme.updated_at.timestamp()}"
                cache.delete(cache_key)
                
                # Clear database cache
                ThemeCache.objects.filter(theme=theme, portal_type=portal_type).delete()
            else:
                # Clear all portal caches for this theme
                for ptype in self.PORTAL_TYPES:
                    cache_key = f"portal_css_{theme.id}_{ptype}_{theme.updated_at.timestamp()}"
                    cache.delete(cache_key)
                
                # Clear all database caches
                ThemeCache.objects.filter(theme=theme).delete()
            
            self.logger.info(f"Cleared theme cache for theme {theme.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to clear theme cache: {str(e)}")
    
    def _get_theme_variations(self, theme: EventTheme) -> Dict[str, Any]:
        """Get available theme variations."""
        variations = {}
        
        try:
            for variation in theme.variations.filter(is_active=True):
                variations[variation.variation_type] = {
                    'css_hash': variation.css_hash,
                    'created_at': variation.created_at,
                }
        except Exception as e:
            self.logger.error(f"Failed to get theme variations: {str(e)}")
        
        return variations
    
    def _apply_default_theme(self, context: Dict[str, Any], portal_type: str) -> Dict[str, Any]:
        """Apply default theme when main theme fails."""
        default_css = self._get_default_css(portal_type)
        
        default_context = {
            'theme': None,
            'theme_css': mark_safe(default_css),
            'theme_colors': {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'accent': '#28a745',
                'neutral_light': '#f8f9fa',
                'neutral_dark': '#343a40',
            },
            'theme_metadata': {
                'portal_type': portal_type,
                'generation_method': 'fallback',
                'wcag_compliant': True,
                'is_fallback': True,
                'last_updated': timezone.now(),
            },
            'theme_variations': {},
        }
        
        enhanced_context = context.copy()
        enhanced_context.update(default_context)
        return enhanced_context
    
    def _get_default_css(self, portal_type: str) -> str:
        """Get default CSS for portal type."""
        default_theme = self.theme_generator.generate_theme({
            'primary_color': '#007bff',
            'secondary_color': '#6c757d',
            'accent_color': '#28a745',
            'neutral_light': '#f8f9fa',
            'neutral_dark': '#343a40',
        })
        
        return create_portal_specific_css(default_theme, portal_type)
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """Validate hex color format."""
        if not color or not isinstance(color, str):
            return False
        
        if not color.startswith('#'):
            return False
        
        if len(color) != 7:
            return False
        
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    def _check_high_contrast(self, color1: str, color2: str) -> bool:
        """Check if two colors have sufficient contrast."""
        try:
            # Simple contrast check (would be more sophisticated in production)
            rgb1 = self._hex_to_rgb(color1)
            rgb2 = self._hex_to_rgb(color2)
            
            # Calculate luminance
            def luminance(rgb):
                r, g, b = [c/255.0 for c in rgb]
                r = r/12.92 if r <= 0.03928 else pow((r + 0.055)/1.055, 2.4)
                g = g/12.92 if g <= 0.03928 else pow((g + 0.055)/1.055, 2.4)
                b = b/12.92 if b <= 0.03928 else pow((b + 0.055)/1.055, 2.4)
                return 0.2126 * r + 0.7152 * g + 0.0722 * b
            
            l1 = luminance(rgb1)
            l2 = luminance(rgb2)
            
            contrast = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
            return contrast >= 4.5  # WCAG AA standard
            
        except Exception:
            return False
    
    def _check_professional_colors(self, theme: EventTheme) -> bool:
        """Check if colors are suitable for professional use."""
        # Simple check - avoid overly bright or saturated colors
        try:
            colors = [theme.primary_color, theme.secondary_color, theme.accent_color]
            
            for color in colors:
                rgb = self._hex_to_rgb(color)
                # Check if any component is too bright (> 240)
                if any(c > 240 for c in rgb):
                    return False
                
                # Check saturation (simplified)
                max_c = max(rgb)
                min_c = min(rgb)
                if max_c > 0:
                    saturation = (max_c - min_c) / max_c
                    if saturation > 0.9:  # Too saturated
                        return False
            
            return True
            
        except Exception:
            return True  # Default to allowing if check fails
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# Django context processor
def theme_context_processor(request):
    """
    Django context processor to inject theme variables into templates.
    
    Usage: Add 'theming.services.portal_renderer.theme_context_processor' 
    to TEMPLATES['OPTIONS']['context_processors'] in settings.py
    """
    context = {}
    
    try:
        # Determine portal type from URL or request
        portal_type = _determine_portal_type(request)
        
        # Get event ID from request (various ways)
        event_id = _get_event_id_from_request(request)
        
        if event_id:
            renderer = PortalRenderer()
            theme = renderer.get_theme_for_event(event_id)
            
            if theme:
                context = renderer.apply_theme(portal_type, theme, context)
            else:
                # Apply default theme
                context = renderer._apply_default_theme(context, portal_type)
        
    except Exception as e:
        logger.error(f"Theme context processor failed: {str(e)}")
        # Return empty context on failure
    
    return context


def _determine_portal_type(request) -> str:
    """Determine portal type from request."""
    path = request.path.lower()
    
    if '/staff/' in path or 'staff' in request.resolver_match.app_name if request.resolver_match else False:
        return 'staff'
    elif '/organizer/' in path or 'organizer' in request.resolver_match.app_name if request.resolver_match else False:
        return 'organizer'
    else:
        return 'participant'  # Default


def _get_event_id_from_request(request) -> Optional[int]:
    """Extract event ID from request."""
    try:
        # Try URL parameters first
        if hasattr(request, 'resolver_match') and request.resolver_match:
            kwargs = request.resolver_match.kwargs
            if 'event_id' in kwargs:
                return int(kwargs['event_id'])
        
        # Try GET parameters
        if 'event_id' in request.GET:
            return int(request.GET['event_id'])
        
        # Try POST parameters
        if 'event_id' in request.POST:
            return int(request.POST['event_id'])
        
        # Try session
        if hasattr(request, 'session') and 'current_event_id' in request.session:
            return int(request.session['current_event_id'])
        
    except (ValueError, TypeError):
        pass
    
    return None


# Template tags would go in a separate file (theming/templatetags/theme_tags.py)
# This is just the service logic