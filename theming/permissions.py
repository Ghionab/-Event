from rest_framework import permissions
from events.models import Event


class IsEventOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an event to edit themes.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions are only allowed to authenticated users
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the event or staff
        if hasattr(obj, 'event'):
            return obj.event.organizer == request.user or request.user.is_staff
        elif hasattr(obj, 'organizer'):
            return obj.organizer == request.user or request.user.is_staff
        
        return request.user.is_staff


class CanModifyTheme(permissions.BasePermission):
    """
    Permission to check if user can modify themes for an event.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get event_id from URL kwargs
        event_id = view.kwargs.get('event_id')
        if not event_id:
            return False
        
        try:
            event = Event.objects.get(id=event_id)
            return event.organizer == request.user or request.user.is_staff
        except Event.DoesNotExist:
            return False


class IsThemeOwner(permissions.BasePermission):
    """
    Permission to check if user owns the theme (through event ownership).
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the event associated with the theme
        if hasattr(obj, 'event'):
            return obj.event.organizer == request.user or request.user.is_staff
        elif hasattr(obj, 'base_theme') and hasattr(obj.base_theme, 'event'):
            return obj.base_theme.event.organizer == request.user or request.user.is_staff
        
        return request.user.is_staff


class CanViewThemeAnalytics(permissions.BasePermission):
    """
    Permission to view theme analytics and cache statistics.
    """
    
    def has_permission(self, request, view):
        # Only staff users can view system-wide analytics
        return request.user.is_authenticated and request.user.is_staff


class CanManageThemeCache(permissions.BasePermission):
    """
    Permission to manage theme cache operations.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get event_id from URL kwargs if available
        event_id = view.kwargs.get('event_id')
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
                return event.organizer == request.user or request.user.is_staff
            except Event.DoesNotExist:
                return False
        
        # For system-wide cache operations, only staff
        return request.user.is_staff


class ThemeGenerationRateLimit(permissions.BasePermission):
    """
    Custom permission to implement rate limiting for theme generation.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Basic rate limiting logic (would be enhanced with Redis in production)
        from django.core.cache import cache
        from django.utils import timezone
        
        # Allow staff users to bypass rate limits
        if request.user.is_staff:
            return True
        
        # Check rate limit for regular users
        cache_key = f"theme_generation_rate_limit_{request.user.id}"
        current_time = timezone.now()
        
        # Get user's recent generation attempts
        recent_attempts = cache.get(cache_key, [])
        
        # Filter attempts from the last hour
        one_hour_ago = current_time.timestamp() - 3600
        recent_attempts = [attempt for attempt in recent_attempts if attempt > one_hour_ago]
        
        # Check if user has exceeded the limit (10 generations per hour)
        if len(recent_attempts) >= 10:
            return False
        
        # Add current attempt and update cache
        recent_attempts.append(current_time.timestamp())
        cache.set(cache_key, recent_attempts, 3600)  # Cache for 1 hour
        
        return True
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)