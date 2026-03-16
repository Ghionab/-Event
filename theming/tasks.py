try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    # Celery not available, create a dummy decorator
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    CELERY_AVAILABLE = False
from django.contrib.auth import get_user_model
from django.utils import timezone
from events.models import Event
from .models import EventTheme, ThemeGenerationLog
from .services.color_extractor import ColorExtractor
from .services.theme_generator import ThemeGenerator
from .services.portal_renderer import PortalRenderer
from .websocket_utils import notify_theme_generation_status
import logging
import time

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_theme_async(self, event_id, user_id=None, image_path=None, algorithm='kmeans'):
    """
    Asynchronously generate theme for an event.
    
    Args:
        event_id: ID of the event to generate theme for
        user_id: ID of the user who requested the generation (optional)
        image_path: Path to the brand asset image (optional)
        algorithm: Color extraction algorithm to use
    
    Returns:
        dict: Generation result with theme data
    """
    start_time = time.time()
    
    try:
        # Get event and user
        event = Event.objects.get(id=event_id)
        user = User.objects.get(id=user_id) if user_id else None
        
        # Notify start of generation
        from .websocket_utils import notify_theme_generation_status, notify_color_extraction_progress
        notify_theme_generation_status(
            event_id=event_id,
            status='processing',
            progress_percentage=10,
            estimated_completion=timezone.now() + timezone.timedelta(minutes=2),
            user_id=user_id
        )
        
        # Log the start of generation
        log_entry = ThemeGenerationLog.log_operation(
            event=event,
            operation_type='generation',
            status='success',  # Will update if it fails
            user=user,
            metadata={
                'async_task_id': self.request.id,
                'algorithm': algorithm,
                'image_path': image_path
            }
        )
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Extracting colors...'}
        )
        
        # Extract colors if image is provided
        extracted_colors = None
        extraction_confidence = 0.8  # Default confidence
        
        if image_path:
            try:
                extractor = ColorExtractor(num_colors=5)
                
                # Notify color extraction progress
                notify_color_extraction_progress(event_id, 25, 'loading_image', user_id)
                
                result = extractor.extract_colors(image_path, algorithm=algorithm)
                
                # Notify color extraction progress
                notify_color_extraction_progress(event_id, 45, 'analyzing_colors', user_id)
                
                extracted_colors = {
                    'primary_color': result.colors[0].color if result.colors else '#007bff',
                    'secondary_color': result.colors[1].color if len(result.colors) > 1 else '#6c757d',
                    'accent_color': result.colors[2].color if len(result.colors) > 2 else '#28a745',
                    'neutral_light': '#f8f9fa',  # Generated
                    'neutral_dark': '#343a40',   # Generated
                }
                extraction_confidence = result.confidence_score
                
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={'current': 50, 'total': 100, 'status': 'Generating theme...'}
                )
                
                # Notify progress
                notify_theme_generation_status(
                    event_id=event_id,
                    status='processing',
                    progress_percentage=50,
                    user_id=user_id
                )
                
            except Exception as e:
                logger.warning(f"Color extraction failed for event {event_id}: {str(e)}")
                # Continue with default colors
                extracted_colors = {
                    'primary_color': '#007bff',
                    'secondary_color': '#6c757d',
                    'accent_color': '#28a745',
                    'neutral_light': '#f8f9fa',
                    'neutral_dark': '#343a40',
                }
        else:
            # Use default colors if no image provided
            extracted_colors = {
                'primary_color': '#007bff',
                'secondary_color': '#6c757d',
                'accent_color': '#28a745',
                'neutral_light': '#f8f9fa',
                'neutral_dark': '#343a40',
            }
        
        # Generate theme CSS
        theme_generator = ThemeGenerator()
        generated_theme = theme_generator.generate_theme(extracted_colors)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Saving theme...'}
        )
        
        # Create or update theme
        theme, created = EventTheme.objects.get_or_create(
            event=event,
            defaults={
                'primary_color': extracted_colors['primary_color'],
                'secondary_color': extracted_colors['secondary_color'],
                'accent_color': extracted_colors['accent_color'],
                'neutral_light': extracted_colors['neutral_light'],
                'neutral_dark': extracted_colors['neutral_dark'],
                'css_content': generated_theme.css_content,
                'generation_method': 'auto',
                'extraction_confidence': extraction_confidence,
                'wcag_compliant': generated_theme.accessibility_compliant,
                'contrast_adjustments_made': generated_theme.contrast_adjustments_made,
            }
        )
        
        if not created:
            # Update existing theme
            theme.primary_color = extracted_colors['primary_color']
            theme.secondary_color = extracted_colors['secondary_color']
            theme.accent_color = extracted_colors['accent_color']
            theme.neutral_light = extracted_colors['neutral_light']
            theme.neutral_dark = extracted_colors['neutral_dark']
            theme.css_content = generated_theme.css_content
            theme.generation_method = 'auto'
            theme.extraction_confidence = extraction_confidence
            theme.wcag_compliant = generated_theme.accessibility_compliant
            theme.contrast_adjustments_made = generated_theme.contrast_adjustments_made
            theme.save()
        
        # Clear any existing cache
        renderer = PortalRenderer()
        renderer.clear_theme_cache(theme)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Update log entry with success
        log_entry.processing_time_ms = processing_time_ms
        log_entry.extraction_confidence = extraction_confidence
        log_entry.save()
        
        # Final progress update
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Theme generation completed'}
        )
        
        # Notify completion
        from .websocket_utils import notify_theme_generation_completed, notify_accessibility_validation_completed
        notify_theme_generation_completed(
            event_id=event_id,
            theme_id=theme.id,
            success=True,
            processing_time_ms=processing_time_ms,
            extraction_confidence=extraction_confidence,
            user_id=user_id
        )
        
        # Notify accessibility validation
        notify_accessibility_validation_completed(
            event_id=event_id,
            theme_id=theme.id,
            wcag_compliant=theme.wcag_compliant,
            adjustments_made=['brightness_adjusted'] if theme.contrast_adjustments_made else [],
            user_id=user_id
        )
        
        return {
            'success': True,
            'theme_id': theme.id,
            'event_id': event_id,
            'processing_time_ms': processing_time_ms,
            'extraction_confidence': extraction_confidence,
            'wcag_compliant': theme.wcag_compliant,
            'contrast_adjustments_made': theme.contrast_adjustments_made
        }
        
    except Event.DoesNotExist:
        error_msg = f"Event with ID {event_id} not found"
        logger.error(error_msg)
        
        notify_theme_generation_status(
            event_id=event_id,
            status='failed',
            error_message=error_msg
        )
        
        return {'success': False, 'error': error_msg}
        
    except Exception as exc:
        error_msg = f"Theme generation failed: {str(exc)}"
        logger.error(f"Theme generation task failed for event {event_id}: {error_msg}")
        
        # Update log entry with failure
        if 'log_entry' in locals():
            log_entry.status = 'failure'
            log_entry.error_message = error_msg
            log_entry.processing_time_ms = int((time.time() - start_time) * 1000)
            log_entry.save()
        
        # Notify failure
        notify_theme_generation_status(
            event_id=event_id,
            status='failed',
            error_message=error_msg
        )
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying theme generation for event {event_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': error_msg}


@shared_task
def cleanup_expired_cache():
    """
    Clean up expired theme cache entries.
    This task should be run periodically (e.g., daily).
    """
    from .models import ThemeCache
    
    try:
        expired_entries = ThemeCache.objects.filter(expires_at__lt=timezone.now())
        count = expired_entries.count()
        expired_entries.delete()
        
        logger.info(f"Cleaned up {count} expired theme cache entries")
        return {'success': True, 'cleaned_entries': count}
        
    except Exception as e:
        logger.error(f"Cache cleanup failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_themes():
    """
    Clean up old unused themes (older than 30 days with no recent access).
    This task should be run periodically (e.g., weekly).
    """
    from django.db.models import Q
    
    try:
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        # Find themes that haven't been accessed in 30 days and have low access count
        old_themes = EventTheme.objects.filter(
            Q(last_accessed__lt=thirty_days_ago) | Q(last_accessed__isnull=True),
            access_count__lt=5,  # Themes with very low usage
            is_fallback=False    # Don't delete fallback themes
        )
        
        count = old_themes.count()
        
        # Log before deletion
        for theme in old_themes:
            ThemeGenerationLog.log_operation(
                event=theme.event,
                operation_type='generation',  # Using existing choice
                status='success',
                metadata={
                    'action': 'theme_cleanup',
                    'reason': 'unused_theme_cleanup',
                    'last_accessed': theme.last_accessed.isoformat() if theme.last_accessed else None,
                    'access_count': theme.access_count
                }
            )
        
        old_themes.delete()
        
        logger.info(f"Cleaned up {count} old unused themes")
        return {'success': True, 'cleaned_themes': count}
        
    except Exception as e:
        logger.error(f"Theme cleanup failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def generate_theme_variations(theme_id, variation_types=None):
    """
    Generate multiple theme variations for a theme.
    
    Args:
        theme_id: ID of the base theme
        variation_types: List of variation types to generate (optional)
    """
    from .models import ThemeVariation
    
    if variation_types is None:
        variation_types = ['light', 'dark', 'high_contrast']
    
    try:
        theme = EventTheme.objects.get(id=theme_id)
        theme_generator = ThemeGenerator()
        
        generated_variations = []
        
        for variation_type in variation_types:
            # Check if variation already exists
            if ThemeVariation.objects.filter(base_theme=theme, variation_type=variation_type).exists():
                continue
            
            try:
                # Generate variation CSS
                variation_css = theme_generator.generate_theme_variation(theme, variation_type)
                
                # Create variation
                variation = ThemeVariation.objects.create(
                    base_theme=theme,
                    variation_type=variation_type,
                    css_content=variation_css
                )
                
                generated_variations.append({
                    'id': variation.id,
                    'type': variation_type,
                    'success': True
                })
                
                # Log the creation
                ThemeGenerationLog.log_operation(
                    event=theme.event,
                    operation_type='variation_created',
                    status='success',
                    metadata={
                        'variation_type': variation_type,
                        'variation_id': variation.id,
                        'async_generation': True
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to generate {variation_type} variation for theme {theme_id}: {str(e)}")
                generated_variations.append({
                    'type': variation_type,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'theme_id': theme_id,
            'generated_variations': generated_variations
        }
        
    except EventTheme.DoesNotExist:
        error_msg = f"Theme with ID {theme_id} not found"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
        
    except Exception as e:
        error_msg = f"Variation generation failed: {str(e)}"
        logger.error(f"Theme variation generation failed for theme {theme_id}: {error_msg}")
        return {'success': False, 'error': error_msg}


@shared_task
def pregenerate_portal_css(theme_id):
    """
    Pre-generate CSS for all portals to improve performance.
    
    Args:
        theme_id: ID of the theme to pre-generate CSS for
    """
    try:
        theme = EventTheme.objects.get(id=theme_id)
        renderer = PortalRenderer()
        
        portal_types = ['staff', 'participant', 'organizer']
        generated_css = {}
        
        for portal_type in portal_types:
            try:
                css_content = renderer.generate_portal_css(theme, portal_type)
                
                # Cache the generated CSS
                cache_key = f"theme_{theme.id}_{portal_type}"
                expires_at = timezone.now() + timezone.timedelta(hours=24)
                
                from .models import ThemeCache
                ThemeCache.objects.update_or_create(
                    cache_key=cache_key,
                    defaults={
                        'theme': theme,
                        'css_content': css_content,
                        'portal_type': portal_type,
                        'expires_at': expires_at
                    }
                )
                
                generated_css[portal_type] = {
                    'success': True,
                    'cache_key': cache_key
                }
                
            except Exception as e:
                logger.error(f"Failed to pre-generate CSS for {portal_type} portal: {str(e)}")
                generated_css[portal_type] = {
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'success': True,
            'theme_id': theme_id,
            'generated_css': generated_css
        }
        
    except EventTheme.DoesNotExist:
        error_msg = f"Theme with ID {theme_id} not found"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
        
    except Exception as e:
        error_msg = f"CSS pre-generation failed: {str(e)}"
        logger.error(f"CSS pre-generation failed for theme {theme_id}: {error_msg}")
        return {'success': False, 'error': error_msg}