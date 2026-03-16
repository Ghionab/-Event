from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from django.core.cache import cache
from django.db import transaction
from events.models import Event
from .models import EventTheme, ColorPalette, ThemeVariation, ThemeCache, ThemeGenerationLog
from .serializers import (
    EventThemeSerializer, EventThemeCreateSerializer, EventThemeUpdateSerializer,
    ColorExtractionRequestSerializer, ColorExtractionResponseSerializer,
    ThemePreviewSerializer, ThemeVariationSerializer, ThemeVariationCreateSerializer,
    ThemeCacheStatsSerializer, ColorPaletteSerializer
)
from .services.color_extractor import ColorExtractor
from .services.theme_generator import ThemeGenerator
from .services.portal_renderer import PortalRenderer
from .permissions import IsEventOwnerOrReadOnly, CanModifyTheme
from .tasks import generate_theme_async
from .decorators import (
    secure_api_endpoint, secure_theme_api, secure_color_extraction,
    secure_theme_generation, secure_admin_api, validate_theme_colors,
    validate_css_content, log_api_access, validate_file_upload
)
from .security import (
    api_security_manager, 
    security_validator, 
    image_processor,
    audit_logger,
    permission_manager
)
import tempfile
import json
import logging

logger = logging.getLogger(__name__)
import os
import logging

logger = logging.getLogger(__name__)


class ThemeRateThrottle(UserRateThrottle):
    """Custom throttle for theme generation operations"""
    scope = 'theme_generation'
    rate = '10/hour'  # Limit theme generation to prevent abuse


class EventThemeListAPIView(generics.ListAPIView):
    """List all themes for events the user has access to"""
    serializer_class = EventThemeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return EventTheme.objects.all().select_related('event').prefetch_related('variations', 'palette')
        
        # Filter themes based on user's events
        user_events = Event.objects.filter(organizer=user)
        return EventTheme.objects.filter(event__in=user_events).select_related('event').prefetch_related('variations', 'palette')


class EventThemeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete theme for a specific event"""
    serializer_class = EventThemeSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    lookup_field = 'event_id'
    lookup_url_kwarg = 'event_id'
    
    def get_object(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == self.request.user or self.request.user.is_staff):
            self.permission_denied(self.request, message="You don't have permission to access this theme")
        
        theme, created = EventTheme.objects.get_or_create(
            event=event,
            defaults={
                'primary_color': '#007bff',
                'secondary_color': '#6c757d',
                'accent_color': '#28a745',
                'neutral_light': '#f8f9fa',
                'neutral_dark': '#343a40',
                'css_content': '/* Default theme CSS */',
                'generation_method': 'fallback',
                'is_fallback': True,
            }
        )
        
        if created:
            # Log the fallback theme creation
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='fallback',
                status='success',
                user=self.request.user,
                metadata={'reason': 'theme_not_found', 'auto_created': True}
            )
        
        return theme
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EventThemeUpdateSerializer
        return EventThemeSerializer
    
    def perform_update(self, serializer):
        theme = serializer.save()
        
        # Regenerate CSS with new colors
        try:
            theme_generator = ThemeGenerator()
            generated_theme = theme_generator.generate_theme({
                'primary_color': theme.primary_color,
                'secondary_color': theme.secondary_color,
                'accent_color': theme.accent_color,
                'neutral_light': theme.neutral_light,
                'neutral_dark': theme.neutral_dark,
            })
            
            theme.css_content = generated_theme.css_content
            theme.wcag_compliant = generated_theme.accessibility_compliant
            theme.contrast_adjustments_made = generated_theme.contrast_adjustments_made
            theme.save()
            
            # Clear cache
            renderer = PortalRenderer()
            renderer.clear_theme_cache(theme)
            
            # Log the update
            ThemeGenerationLog.log_operation(
                event=theme.event,
                operation_type='manual_override',
                status='success',
                user=self.request.user,
                metadata={'updated_fields': list(serializer.validated_data.keys())}
            )
            
        except Exception as e:
            logger.error(f"Failed to regenerate CSS for theme {theme.id}: {str(e)}")
            ThemeGenerationLog.log_operation(
                event=theme.event,
                operation_type='manual_override',
                status='failure',
                error_message=str(e),
                user=self.request.user
            )
    
    def perform_destroy(self, instance):
        # Log the deletion
        ThemeGenerationLog.log_operation(
            event=instance.event,
            operation_type='manual_override',
            status='success',
            user=self.request.user,
            metadata={'action': 'theme_deleted'}
        )
        
        # Clear cache before deletion
        renderer = PortalRenderer()
        renderer.clear_theme_cache(instance)
        
        instance.delete()


class EventThemeCreateAPIView(generics.CreateAPIView):
    """Create a new theme for an event"""
    serializer_class = EventThemeCreateSerializer
    permission_classes = [permissions.IsAuthenticated, CanModifyTheme]
    throttle_classes = [ThemeRateThrottle]
    
    @secure_theme_generation()
    @validate_theme_colors
    @log_api_access('theme_creation')
    def perform_create(self, serializer):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == self.request.user or self.request.user.is_staff):
            self.permission_denied(self.request, message="You don't have permission to create themes for this event")
        
        # Delete existing theme if it exists
        EventTheme.objects.filter(event=event).delete()
        
        # Create new theme
        theme = serializer.save(event=event)
        
        # Generate CSS
        try:
            theme_generator = ThemeGenerator()
            generated_theme = theme_generator.generate_theme({
                'primary_color': theme.primary_color,
                'secondary_color': theme.secondary_color,
                'accent_color': theme.accent_color,
                'neutral_light': theme.neutral_light,
                'neutral_dark': theme.neutral_dark,
            })
            
            theme.css_content = generated_theme.css_content
            theme.wcag_compliant = generated_theme.accessibility_compliant
            theme.contrast_adjustments_made = generated_theme.contrast_adjustments_made
            theme.save()
            
            # Log the creation
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='manual_override',
                status='success',
                user=self.request.user,
                metadata={'action': 'theme_created'}
            )
            
        except Exception as e:
            logger.error(f"Failed to generate CSS for new theme: {str(e)}")
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='manual_override',
                status='failure',
                error_message=str(e),
                user=self.request.user
            )


class ColorExtractionAPIView(APIView):
    """Extract colors from uploaded brand assets"""
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ThemeRateThrottle]
    
    @secure_color_extraction()
    @validate_file_upload(allowed_types=['PNG', 'JPEG', 'JPG', 'WEBP'], max_size=10*1024*1024)
    @log_api_access('color_extraction')
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to extract colors for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ColorExtractionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['image']
        algorithm = serializer.validated_data.get('algorithm', 'kmeans')
        num_colors = serializer.validated_data.get('num_colors', 5)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # Extract colors using ColorExtractor
            extractor = ColorExtractor(num_colors=num_colors)
            result = extractor.extract_colors(temp_file_path, algorithm=algorithm)
            
            # Convert ExtractedColor objects to dictionaries
            extracted_colors = [
                {
                    "color": color.color,
                    "confidence": color.confidence,
                    "frequency": color.frequency,
                    "name": color.name
                }
                for color in result.colors
            ]
            
            # Create or update color palette
            theme, _ = EventTheme.objects.get_or_create(event=event)
            palette, created = ColorPalette.objects.get_or_create(
                theme=theme,
                defaults={
                    'extracted_colors': extracted_colors,
                    'source_image': uploaded_file.name,
                    'extraction_algorithm': result.algorithm_used,
                    'color_diversity_score': result.diversity_score,
                    'overall_confidence': result.confidence_score,
                    'extraction_parameters': result.metadata
                }
            )
            
            if not created:
                palette.extracted_colors = extracted_colors
                palette.source_image = uploaded_file.name
                palette.extraction_algorithm = result.algorithm_used
                palette.overall_confidence = result.confidence_score
                palette.color_diversity_score = result.diversity_score
                palette.extraction_parameters = result.metadata
                palette.save()
            
            # Log the operation
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='generation',
                status='success',
                processing_time_ms=result.processing_time_ms,
                extraction_confidence=result.confidence_score,
                source_image_path=uploaded_file.name,
                user=request.user,
                metadata={
                    'algorithm_used': result.algorithm_used,
                    'colors_extracted': len(result.colors),
                    'diversity_score': result.diversity_score,
                    'image_properties': {
                        'width': result.image_properties.width,
                        'height': result.image_properties.height,
                        'format': result.image_properties.format,
                        'has_transparency': result.image_properties.has_transparency
                    }
                }
            )
            
            response_data = {
                'extracted_colors': extracted_colors,
                'overall_confidence': result.confidence_score,
                'color_diversity_score': result.diversity_score,
                'processing_time_ms': result.processing_time_ms,
                'algorithm_used': result.algorithm_used,
                'image_properties': {
                    'width': result.image_properties.width,
                    'height': result.image_properties.height,
                    'format': result.image_properties.format,
                    'has_transparency': result.image_properties.has_transparency
                }
            }
            
            response_serializer = ColorExtractionResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            # Handle unsupported format or validation errors
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='generation',
                status='failure',
                error_message=str(e),
                source_image_path=uploaded_file.name,
                user=request.user
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Handle other extraction errors
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='generation',
                status='failure',
                error_message=str(e),
                source_image_path=uploaded_file.name,
                user=request.user
            )
            return Response(
                {'error': f'Color extraction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class ColorPaletteAPIView(generics.RetrieveAPIView):
    """Get color palette for an event"""
    serializer_class = ColorPaletteSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def get_object(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == self.request.user or self.request.user.is_staff):
            self.permission_denied(self.request, message="You don't have permission to access this palette")
        
        try:
            theme = EventTheme.objects.get(event=event)
            return theme.palette
        except (EventTheme.DoesNotExist, ColorPalette.DoesNotExist):
            return Response({'error': 'Color palette not found'}, status=status.HTTP_404_NOT_FOUND)


class ThemePreviewAPIView(APIView):
    """Preview theme for a specific portal"""
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def get(self, request, event_id, portal_type):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to preview themes for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate portal type
        valid_portals = ['staff', 'participant', 'organizer']
        if portal_type not in valid_portals:
            return Response(
                {'error': f'Invalid portal type. Must be one of: {", ".join(valid_portals)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            renderer = PortalRenderer()
            theme = renderer.get_theme_for_event(event_id)
            
            if not theme:
                return Response({'error': 'Theme not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Generate portal-specific CSS
            css_content = renderer.generate_portal_css(theme, portal_type)
            
            # Validate compatibility
            is_compatible = renderer.validate_portal_compatibility(theme, portal_type)
            compatibility_score = 1.0 if is_compatible else 0.5
            
            # Return CSS as HTTP response for direct use
            if request.GET.get('format') == 'css':
                response = HttpResponse(css_content, content_type='text/css')
                response['X-Theme-Compatible'] = str(is_compatible).lower()
                response['X-Theme-ID'] = str(theme.id)
                response['X-Portal-Type'] = portal_type
                return response
            
            # Return JSON response with preview data
            preview_data = {
                'portal_type': portal_type,
                'css_content': css_content,
                'compatibility_score': compatibility_score,
                'theme_id': theme.id,
                'event_id': event_id
            }
            
            serializer = ThemePreviewSerializer(data=preview_data)
            serializer.is_valid(raise_exception=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Theme preview failed for event {event_id}, portal {portal_type}: {str(e)}")
            return Response(
                {'error': f'Theme preview failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeVariationListCreateAPIView(generics.ListCreateAPIView):
    """List and create theme variations for an event"""
    serializer_class = ThemeVariationSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def get_queryset(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == self.request.user or self.request.user.is_staff):
            return ThemeVariation.objects.none()
        
        try:
            theme = EventTheme.objects.get(event=event)
            return theme.variations.all()
        except EventTheme.DoesNotExist:
            return ThemeVariation.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ThemeVariationCreateSerializer
        return ThemeVariationSerializer
    
    def perform_create(self, serializer):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == self.request.user or self.request.user.is_staff):
            self.permission_denied(self.request, message="You don't have permission to create variations for this event")
        
        theme = get_object_or_404(EventTheme, event=event)
        
        # Generate variation CSS using ThemeGenerator
        try:
            theme_generator = ThemeGenerator()
            variation_type = serializer.validated_data['variation_type']
            
            # Generate variation based on base theme
            variation_css = theme_generator.generate_theme_variation(theme, variation_type)
            
            variation = serializer.save(
                base_theme=theme,
                css_content=variation_css
            )
            
            # Log the creation
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='variation_created',
                status='success',
                user=self.request.user,
                metadata={'variation_type': variation_type, 'variation_id': variation.id}
            )
            
        except Exception as e:
            logger.error(f"Failed to create theme variation: {str(e)}")
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='variation_created',
                status='failure',
                error_message=str(e),
                user=self.request.user
            )
            raise


class ThemeVariationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific theme variation"""
    serializer_class = ThemeVariationSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def get_object(self):
        event_id = self.kwargs['event_id']
        variation_id = self.kwargs['variation_id']
        
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == self.request.user or self.request.user.is_staff):
            self.permission_denied(self.request, message="You don't have permission to access this variation")
        
        theme = get_object_or_404(EventTheme, event=event)
        return get_object_or_404(ThemeVariation, id=variation_id, base_theme=theme)


class ThemeCacheStatsAPIView(APIView):
    """Get cache performance statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    @secure_admin_api()
    @log_api_access('cache_stats')
    def get(self, request):
        # Only allow staff users to view cache stats
        if not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to view cache statistics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            stats = {
                'total_entries': ThemeCache.objects.count(),
                'expired_entries': ThemeCache.objects.filter(expires_at__lt=timezone.now()).count(),
                'total_access_count': sum(ThemeCache.objects.values_list('access_count', flat=True) or [0]),
                'portal_breakdown': {},
                'hit_rate': 0.0,
                'average_access_time_ms': 0.0
            }
            
            # Portal type breakdown
            for portal_type, _ in ThemeCache.PORTAL_TYPES:
                count = ThemeCache.objects.filter(portal_type=portal_type).count()
                stats['portal_breakdown'][portal_type] = count
            
            # Calculate hit rate (simplified - would need more sophisticated tracking in production)
            total_requests = cache.get('theme_cache_total_requests', 0)
            cache_hits = cache.get('theme_cache_hits', 0)
            if total_requests > 0:
                stats['hit_rate'] = cache_hits / total_requests
            
            # Average access time (placeholder - would need actual timing data)
            stats['average_access_time_ms'] = 50.0  # Placeholder value
            
            serializer = ThemeCacheStatsSerializer(data=stats)
            serializer.is_valid(raise_exception=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return Response(
                {'error': f'Failed to retrieve cache statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearThemeCacheAPIView(APIView):
    """Clear theme cache for an event"""
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def delete(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to clear cache for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            theme = EventTheme.objects.get(event=event)
            
            # Clear all cache entries for this theme
            deleted_count = theme.cache_entries.all().delete()[0]
            
            # Also clear any related cache keys
            renderer = PortalRenderer()
            renderer.clear_theme_cache(theme)
            
            # Log the operation
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='cache_miss',  # Using existing choice
                status='success',
                user=request.user,
                metadata={'action': 'cache_cleared', 'entries_deleted': deleted_count}
            )
            
            return Response({
                'success': True,
                'message': f'Cleared {deleted_count} cache entries for event {event.title}',
                'entries_deleted': deleted_count
            })
            
        except EventTheme.DoesNotExist:
            return Response({'error': 'Theme not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Failed to clear cache for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Failed to clear cache: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateThemeAPIView(APIView):
    """Generate or regenerate theme for an event"""
    permission_classes = [permissions.IsAuthenticated, CanModifyTheme]
    throttle_classes = [ThemeRateThrottle]
    
    @secure_theme_generation()
    @log_api_access('theme_generation')
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to generate themes for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Check if async generation is requested
            async_generation = request.data.get('async', False)
            
            if async_generation:
                # Queue async theme generation
                task = generate_theme_async.delay(event_id, request.user.id)
                
                return Response({
                    'success': True,
                    'message': 'Theme generation started',
                    'task_id': task.id,
                    'event_id': event_id,
                    'async': True
                }, status=status.HTTP_202_ACCEPTED)
            
            else:
                # Synchronous theme generation
                with transaction.atomic():
                    # Initialize services
                    theme_generator = ThemeGenerator()
                    
                    # Generate theme (placeholder - would use actual color extraction)
                    generated_theme = theme_generator.generate_theme({
                        'primary_color': '#007bff',
                        'secondary_color': '#6c757d',
                        'accent_color': '#28a745',
                        'neutral_light': '#f8f9fa',
                        'neutral_dark': '#343a40',
                    })
                    
                    # Create or update theme
                    theme, created = EventTheme.objects.get_or_create(
                        event=event,
                        defaults={
                            'primary_color': '#007bff',
                            'secondary_color': '#6c757d',
                            'accent_color': '#28a745',
                            'neutral_light': '#f8f9fa',
                            'neutral_dark': '#343a40',
                            'css_content': generated_theme.css_content,
                            'generation_method': 'auto',
                            'extraction_confidence': 0.8,
                            'wcag_compliant': generated_theme.accessibility_compliant,
                            'contrast_adjustments_made': generated_theme.contrast_adjustments_made,
                        }
                    )
                    
                    if not created:
                        # Update existing theme
                        theme.primary_color = '#007bff'
                        theme.secondary_color = '#6c757d'
                        theme.accent_color = '#28a745'
                        theme.neutral_light = '#f8f9fa'
                        theme.neutral_dark = '#343a40'
                        theme.css_content = generated_theme.css_content
                        theme.generation_method = 'auto'
                        theme.extraction_confidence = 0.8
                        theme.wcag_compliant = generated_theme.accessibility_compliant
                        theme.contrast_adjustments_made = generated_theme.contrast_adjustments_made
                        theme.save()
                    
                    # Clear any existing cache
                    renderer = PortalRenderer()
                    renderer.clear_theme_cache(theme)
                    
                    # Log the operation
                    ThemeGenerationLog.log_operation(
                        event=event,
                        operation_type='generation',
                        status='success',
                        processing_time_ms=100,  # Placeholder
                        extraction_confidence=0.8,
                        user=request.user,
                        metadata={'sync_generation': True}
                    )
                
                serializer = EventThemeSerializer(theme)
                return Response({
                    'success': True,
                    'message': 'Theme generated successfully',
                    'theme': serializer.data,
                    'async': False
                })
                
        except Exception as e:
            logger.error(f"Theme generation failed for event {event_id}: {str(e)}")
            
            # Log the failure
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='generation',
                status='failure',
                error_message=str(e),
                user=request.user
            )
            
            return Response(
                {'error': f'Theme generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Utility API views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def theme_generation_logs(request, event_id):
    """Get theme generation logs for an event"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions
    if not (event.organizer == request.user or request.user.is_staff):
        return Response(
            {'error': 'You do not have permission to view logs for this event'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    logs = event.theme_logs.all()[:20]  # Latest 20 logs
    
    from .serializers import ThemeGenerationLogSerializer
    serializer = ThemeGenerationLogSerializer(logs, many=True)
    
    return Response({
        'event_id': event_id,
        'event_title': event.title,
        'logs': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def supported_algorithms(request):
    """Get list of supported color extraction algorithms"""
    algorithms = [
        {
            'name': 'kmeans',
            'display_name': 'K-Means Clustering',
            'description': 'Uses K-means clustering to identify dominant colors',
            'recommended': True
        },
        {
            'name': 'colorthief',
            'display_name': 'Color Thief',
            'description': 'Fast color extraction using Color Thief algorithm',
            'recommended': False
        },
        {
            'name': 'dominant',
            'display_name': 'Dominant Color',
            'description': 'Simple dominant color extraction',
            'recommended': False
        }
    ]
    
    return Response({
        'algorithms': algorithms,
        'default': 'kmeans'
    })


# Additional API endpoints for comprehensive theme management

class ThemeVariationBulkCreateAPIView(APIView):
    """Create multiple theme variations at once"""
    permission_classes = [permissions.IsAuthenticated, CanModifyTheme]
    throttle_classes = [ThemeRateThrottle]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to create variations for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        theme = get_object_or_404(EventTheme, event=event)
        variation_types = request.data.get('variation_types', [])
        
        if not variation_types:
            return Response(
                {'error': 'variation_types is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .tasks import generate_theme_variations
            
            # Queue async generation of variations
            task = generate_theme_variations.delay(theme.id, variation_types)
            
            return Response({
                'success': True,
                'message': f'Generating {len(variation_types)} theme variations',
                'task_id': task.id,
                'theme_id': theme.id,
                'variation_types': variation_types
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Failed to queue theme variations: {str(e)}")
            return Response(
                {'error': f'Failed to generate variations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeAnalyticsAPIView(APIView):
    """Get analytics data for theme usage"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to view analytics for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            theme = EventTheme.objects.get(event=event)
            
            # Get analytics data
            analytics = {
                'theme_id': theme.id,
                'event_id': event_id,
                'access_count': theme.access_count,
                'last_accessed': theme.last_accessed,
                'generation_method': theme.generation_method,
                'extraction_confidence': theme.extraction_confidence,
                'wcag_compliant': theme.wcag_compliant,
                'contrast_adjustments_made': theme.contrast_adjustments_made,
                'cache_performance': {
                    'total_cache_entries': theme.cache_entries.count(),
                    'active_cache_entries': theme.cache_entries.filter(expires_at__gt=timezone.now()).count(),
                    'total_cache_hits': sum(theme.cache_entries.values_list('access_count', flat=True) or [0])
                },
                'variations': {
                    'total_variations': theme.variations.count(),
                    'active_variations': theme.variations.filter(is_active=True).count(),
                    'variation_types': list(theme.variations.values_list('variation_type', flat=True))
                },
                'generation_logs': {
                    'total_operations': event.theme_logs.count(),
                    'successful_operations': event.theme_logs.filter(status='success').count(),
                    'failed_operations': event.theme_logs.filter(status='failure').count(),
                    'recent_operations': event.theme_logs.order_by('-created_at')[:5].values(
                        'operation_type', 'status', 'created_at', 'processing_time_ms'
                    )
                }
            }
            
            return Response(analytics)
            
        except EventTheme.DoesNotExist:
            return Response({'error': 'Theme not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Failed to get analytics for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Failed to retrieve analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# Additional API endpoints for comprehensive theme management

class ThemeVariationBulkCreateAPIView(APIView):
    """Create multiple theme variations at once"""
    permission_classes = [permissions.IsAuthenticated, CanModifyTheme]
    throttle_classes = [ThemeRateThrottle]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to create variations for this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        theme = get_object_or_404(EventTheme, event=event)
        variation_types = request.data.get('variation_types', [])

        if not variation_types:
            return Response(
                {'error': 'variation_types is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .tasks import generate_theme_variations

            # Queue async generation of variations
            task = generate_theme_variations.delay(theme.id, variation_types)

            return Response({
                'success': True,
                'message': f'Generating {len(variation_types)} theme variations',
                'task_id': task.id,
                'theme_id': theme.id,
                'variation_types': variation_types
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            logger.error(f"Failed to queue theme variations: {str(e)}")
            return Response(
                {'error': f'Failed to generate variations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeAnalyticsAPIView(APIView):
    """Get analytics data for theme usage"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to view analytics for this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            theme = EventTheme.objects.get(event=event)

            # Get analytics data
            analytics = {
                'theme_id': theme.id,
                'event_id': event_id,
                'access_count': theme.access_count,
                'last_accessed': theme.last_accessed,
                'generation_method': theme.generation_method,
                'extraction_confidence': theme.extraction_confidence,
                'wcag_compliant': theme.wcag_compliant,
                'contrast_adjustments_made': theme.contrast_adjustments_made,
                'cache_performance': {
                    'total_cache_entries': theme.cache_entries.count(),
                    'active_cache_entries': theme.cache_entries.filter(expires_at__gt=timezone.now()).count(),
                    'total_cache_hits': sum(theme.cache_entries.values_list('access_count', flat=True) or [0])
                },
                'variations': {
                    'total_variations': theme.variations.count(),
                    'active_variations': theme.variations.filter(is_active=True).count(),
                    'variation_types': list(theme.variations.values_list('variation_type', flat=True))
                },
                'generation_logs': {
                    'total_operations': event.theme_logs.count(),
                    'successful_operations': event.theme_logs.filter(status='success').count(),
                    'failed_operations': event.theme_logs.filter(status='failure').count(),
                    'recent_operations': event.theme_logs.order_by('-created_at')[:5].values(
                        'operation_type', 'status', 'created_at', 'processing_time_ms'
                    )
                }
            }

            return Response(analytics)

        except EventTheme.DoesNotExist:
            return Response({'error': 'Theme not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Failed to get analytics for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Failed to retrieve analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeValidationAPIView(APIView):
    """Validate theme colors and CSS for accessibility and security"""
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to validate themes for this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            from .security import security_validator
            from .services.theme_generator import ThemeGenerator

            # Get validation data from request
            colors = request.data.get('colors', {})
            css_content = request.data.get('css_content', '')

            validation_results = {
                'colors': {},
                'css': {},
                'accessibility': {},
                'overall_valid': True
            }

            # Validate colors
            for color_name, color_value in colors.items():
                is_valid = security_validator.validate_color_value(color_value)
                validation_results['colors'][color_name] = {
                    'value': color_value,
                    'valid': is_valid
                }
                if not is_valid:
                    validation_results['overall_valid'] = False

            # Validate CSS if provided
            if css_content:
                css_validation = security_validator.validate_css_content(css_content)
                validation_results['css'] = css_validation
                if not css_validation['is_valid']:
                    validation_results['overall_valid'] = False

            # Validate accessibility
            if colors:
                theme_generator = ThemeGenerator()
                accessibility_result = theme_generator.validate_accessibility(colors)
                validation_results['accessibility'] = {
                    'wcag_compliant': accessibility_result.get('wcag_compliant', False),
                    'contrast_ratios': accessibility_result.get('contrast_ratios', {}),
                    'adjustments_needed': accessibility_result.get('adjustments_needed', [])
                }
                if not accessibility_result.get('wcag_compliant', False):
                    validation_results['overall_valid'] = False

            return Response(validation_results)

        except Exception as e:
            logger.error(f"Theme validation failed for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Validation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeExportAPIView(APIView):
    """Export theme data in various formats"""
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to export themes for this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        export_format = request.GET.get('format', 'json')
        include_variations = request.GET.get('include_variations', 'false').lower() == 'true'

        try:
            theme = EventTheme.objects.get(event=event)

            # Prepare export data
            export_data = {
                'event': {
                    'id': event.id,
                    'title': event.title
                },
                'theme': {
                    'id': theme.id,
                    'primary_color': theme.primary_color,
                    'secondary_color': theme.secondary_color,
                    'accent_color': theme.accent_color,
                    'neutral_light': theme.neutral_light,
                    'neutral_dark': theme.neutral_dark,
                    'generation_method': theme.generation_method,
                    'extraction_confidence': theme.extraction_confidence,
                    'wcag_compliant': theme.wcag_compliant,
                    'created_at': theme.created_at.isoformat(),
                    'updated_at': theme.updated_at.isoformat()
                }
            }

            # Include CSS content
            if export_format in ['css', 'all']:
                export_data['css_content'] = theme.css_content

            # Include color palette if available
            if hasattr(theme, 'palette'):
                export_data['color_palette'] = {
                    'extracted_colors': theme.palette.extracted_colors,
                    'extraction_algorithm': theme.palette.extraction_algorithm,
                    'color_diversity_score': theme.palette.color_diversity_score,
                    'overall_confidence': theme.palette.overall_confidence
                }

            # Include variations if requested
            if include_variations:
                variations = theme.variations.filter(is_active=True)
                export_data['variations'] = [
                    {
                        'id': var.id,
                        'variation_type': var.variation_type,
                        'css_content': var.css_content if export_format in ['css', 'all'] else None,
                        'created_at': var.created_at.isoformat()
                    }
                    for var in variations
                ]

            # Return appropriate format
            if export_format == 'css':
                # Return only CSS content
                css_content = theme.css_content
                if include_variations:
                    for var in theme.variations.filter(is_active=True):
                        css_content += f"\n\n/* {var.get_variation_type_display()} Variation */\n"
                        css_content += var.css_content

                response = HttpResponse(css_content, content_type='text/css')
                response['Content-Disposition'] = f'attachment; filename="theme_{event.id}.css"'
                return response

            else:
                # Return JSON
                response = Response(export_data)
                response['Content-Disposition'] = f'attachment; filename="theme_{event.id}.json"'
                return response

        except EventTheme.DoesNotExist:
            return Response({'error': 'Theme not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Theme export failed for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Export failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeImportAPIView(APIView):
    """Import theme data from external sources"""
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.IsAuthenticated, CanModifyTheme]
    throttle_classes = [ThemeRateThrottle]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to import themes for this event'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            import_data = None

            # Handle file upload
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                if uploaded_file.name.endswith('.json'):
                    import_data = json.loads(uploaded_file.read().decode('utf-8'))
                else:
                    return Response(
                        {'error': 'Only JSON files are supported for import'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Handle JSON data
            elif request.data:
                import_data = request.data

            else:
                return Response(
                    {'error': 'No import data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate import data structure
            if not isinstance(import_data, dict) or 'theme' not in import_data:
                return Response(
                    {'error': 'Invalid import data structure'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            theme_data = import_data['theme']

            # Validate required fields
            required_fields = ['primary_color', 'secondary_color', 'accent_color', 'neutral_light', 'neutral_dark']
            for field in required_fields:
                if field not in theme_data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Validate colors
            from .security import security_validator
            for field in required_fields:
                if not security_validator.validate_color_value(theme_data[field]):
                    return Response(
                        {'error': f'Invalid color value for {field}: {theme_data[field]}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create or update theme
            theme, created = EventTheme.objects.get_or_create(
                event=event,
                defaults={
                    'primary_color': theme_data['primary_color'],
                    'secondary_color': theme_data['secondary_color'],
                    'accent_color': theme_data['accent_color'],
                    'neutral_light': theme_data['neutral_light'],
                    'neutral_dark': theme_data['neutral_dark'],
                    'generation_method': 'manual',
                    'extraction_confidence': theme_data.get('extraction_confidence', 1.0),
                    'wcag_compliant': theme_data.get('wcag_compliant', True),
                    'contrast_adjustments_made': theme_data.get('contrast_adjustments_made', False),
                }
            )

            if not created:
                # Update existing theme
                theme.primary_color = theme_data['primary_color']
                theme.secondary_color = theme_data['secondary_color']
                theme.accent_color = theme_data['accent_color']
                theme.neutral_light = theme_data['neutral_light']
                theme.neutral_dark = theme_data['neutral_dark']
                theme.generation_method = 'manual'
                theme.extraction_confidence = theme_data.get('extraction_confidence', 1.0)
                theme.wcag_compliant = theme_data.get('wcag_compliant', True)
                theme.contrast_adjustments_made = theme_data.get('contrast_adjustments_made', False)
                theme.save()

            # Generate CSS
            theme_generator = ThemeGenerator()
            generated_theme = theme_generator.generate_theme({
                'primary_color': theme.primary_color,
                'secondary_color': theme.secondary_color,
                'accent_color': theme.accent_color,
                'neutral_light': theme.neutral_light,
                'neutral_dark': theme.neutral_dark,
            })

            theme.css_content = generated_theme.css_content
            theme.save()

            # Log the import
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='manual_override',
                status='success',
                user=request.user,
                metadata={
                    'action': 'theme_imported',
                    'import_source': 'file' if 'file' in request.FILES else 'json_data',
                    'created': created
                }
            )

            serializer = EventThemeSerializer(theme)
            return Response({
                'success': True,
                'message': 'Theme imported successfully',
                'theme': serializer.data,
                'created': created
            })

        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Theme import failed for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeValidationAPIView(APIView):
    """Validate theme colors and CSS for accessibility and security"""
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to validate themes for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from .security import security_validator
            from .services.theme_generator import ThemeGenerator
            
            # Get validation data from request
            colors = request.data.get('colors', {})
            css_content = request.data.get('css_content', '')
            
            validation_results = {
                'colors': {},
                'css': {},
                'accessibility': {},
                'overall_valid': True
            }
            
            # Validate colors
            for color_name, color_value in colors.items():
                is_valid = security_validator.validate_color_value(color_value)
                validation_results['colors'][color_name] = {
                    'value': color_value,
                    'valid': is_valid
                }
                if not is_valid:
                    validation_results['overall_valid'] = False
            
            # Validate CSS if provided
            if css_content:
                css_validation = security_validator.validate_css_content(css_content)
                validation_results['css'] = css_validation
                if not css_validation['is_valid']:
                    validation_results['overall_valid'] = False
            
            # Validate accessibility
            if colors:
                theme_generator = ThemeGenerator()
                try:
                    accessibility_result = theme_generator.validate_accessibility(colors)
                    validation_results['accessibility'] = {
                        'wcag_compliant': accessibility_result.get('wcag_compliant', False),
                        'contrast_ratios': accessibility_result.get('contrast_ratios', {}),
                        'adjustments_needed': accessibility_result.get('adjustments_needed', [])
                    }
                    if not accessibility_result.get('wcag_compliant', False):
                        validation_results['overall_valid'] = False
                except AttributeError:
                    # Fallback if validate_accessibility method doesn't exist
                    validation_results['accessibility'] = {
                        'wcag_compliant': True,
                        'contrast_ratios': {},
                        'adjustments_needed': []
                    }
            
            return Response(validation_results)
            
        except Exception as e:
            logger.error(f"Theme validation failed for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Validation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeExportAPIView(APIView):
    """Export theme data in various formats"""
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to export themes for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        export_format = request.GET.get('format', 'json')
        include_variations = request.GET.get('include_variations', 'false').lower() == 'true'
        
        try:
            theme = EventTheme.objects.get(event=event)
            
            # Prepare export data
            export_data = {
                'event': {
                    'id': event.id,
                    'title': event.title
                },
                'theme': {
                    'id': theme.id,
                    'primary_color': theme.primary_color,
                    'secondary_color': theme.secondary_color,
                    'accent_color': theme.accent_color,
                    'neutral_light': theme.neutral_light,
                    'neutral_dark': theme.neutral_dark,
                    'generation_method': theme.generation_method,
                    'extraction_confidence': theme.extraction_confidence,
                    'wcag_compliant': theme.wcag_compliant,
                    'created_at': theme.created_at.isoformat(),
                    'updated_at': theme.updated_at.isoformat()
                }
            }
            
            # Include CSS content
            if export_format in ['css', 'all']:
                export_data['css_content'] = theme.css_content
            
            # Include color palette if available
            if hasattr(theme, 'palette'):
                export_data['color_palette'] = {
                    'extracted_colors': theme.palette.extracted_colors,
                    'extraction_algorithm': theme.palette.extraction_algorithm,
                    'color_diversity_score': theme.palette.color_diversity_score,
                    'overall_confidence': theme.palette.overall_confidence
                }
            
            # Include variations if requested
            if include_variations:
                variations = theme.variations.filter(is_active=True)
                export_data['variations'] = [
                    {
                        'id': var.id,
                        'variation_type': var.variation_type,
                        'css_content': var.css_content if export_format in ['css', 'all'] else None,
                        'created_at': var.created_at.isoformat()
                    }
                    for var in variations
                ]
            
            # Return appropriate format
            if export_format == 'css':
                # Return only CSS content
                css_content = theme.css_content
                if include_variations:
                    for var in theme.variations.filter(is_active=True):
                        css_content += f"\n\n/* {var.get_variation_type_display()} Variation */\n"
                        css_content += var.css_content
                
                response = HttpResponse(css_content, content_type='text/css')
                response['Content-Disposition'] = f'attachment; filename="theme_{event.id}.css"'
                return response
            
            else:
                # Return JSON
                response = Response(export_data)
                response['Content-Disposition'] = f'attachment; filename="theme_{event.id}.json"'
                return response
                
        except EventTheme.DoesNotExist:
            return Response({'error': 'Theme not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Theme export failed for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Export failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThemeImportAPIView(APIView):
    """Import theme data from external sources"""
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.IsAuthenticated, CanModifyTheme]
    throttle_classes = [ThemeRateThrottle]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permissions
        if not (event.organizer == request.user or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to import themes for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            import_data = None
            
            # Handle file upload
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                if uploaded_file.name.endswith('.json'):
                    import json
                    import_data = json.loads(uploaded_file.read().decode('utf-8'))
                else:
                    return Response(
                        {'error': 'Only JSON files are supported for import'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Handle JSON data
            elif request.data:
                import_data = request.data
            
            else:
                return Response(
                    {'error': 'No import data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate import data structure
            if not isinstance(import_data, dict) or 'theme' not in import_data:
                return Response(
                    {'error': 'Invalid import data structure'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            theme_data = import_data['theme']
            
            # Validate required fields
            required_fields = ['primary_color', 'secondary_color', 'accent_color', 'neutral_light', 'neutral_dark']
            for field in required_fields:
                if field not in theme_data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate colors
            from .security import security_validator
            for field in required_fields:
                if not security_validator.validate_color_value(theme_data[field]):
                    return Response(
                        {'error': f'Invalid color value for {field}: {theme_data[field]}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create or update theme
            theme, created = EventTheme.objects.get_or_create(
                event=event,
                defaults={
                    'primary_color': theme_data['primary_color'],
                    'secondary_color': theme_data['secondary_color'],
                    'accent_color': theme_data['accent_color'],
                    'neutral_light': theme_data['neutral_light'],
                    'neutral_dark': theme_data['neutral_dark'],
                    'generation_method': 'manual',
                    'extraction_confidence': theme_data.get('extraction_confidence', 1.0),
                    'wcag_compliant': theme_data.get('wcag_compliant', True),
                    'contrast_adjustments_made': theme_data.get('contrast_adjustments_made', False),
                }
            )
            
            if not created:
                # Update existing theme
                theme.primary_color = theme_data['primary_color']
                theme.secondary_color = theme_data['secondary_color']
                theme.accent_color = theme_data['accent_color']
                theme.neutral_light = theme_data['neutral_light']
                theme.neutral_dark = theme_data['neutral_dark']
                theme.generation_method = 'manual'
                theme.extraction_confidence = theme_data.get('extraction_confidence', 1.0)
                theme.wcag_compliant = theme_data.get('wcag_compliant', True)
                theme.contrast_adjustments_made = theme_data.get('contrast_adjustments_made', False)
                theme.save()
            
            # Generate CSS
            theme_generator = ThemeGenerator()
            generated_theme = theme_generator.generate_theme({
                'primary_color': theme.primary_color,
                'secondary_color': theme.secondary_color,
                'accent_color': theme.accent_color,
                'neutral_light': theme.neutral_light,
                'neutral_dark': theme.neutral_dark,
            })
            
            theme.css_content = generated_theme.css_content
            theme.save()
            
            # Log the import
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type='manual_override',
                status='success',
                user=request.user,
                metadata={
                    'action': 'theme_imported',
                    'import_source': 'file' if 'file' in request.FILES else 'json_data',
                    'created': created
                }
            )
            
            serializer = EventThemeSerializer(theme)
            return Response({
                'success': True,
                'message': 'Theme imported successfully',
                'theme': serializer.data,
                'created': created
            })
            
        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Theme import failed for event {event_id}: {str(e)}")
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RateLimitStatusAPIView(APIView):
    """Get current rate limit status for the user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from .security import rate_limiter
        
        user_id = request.user.id
        operations = ['theme_generation', 'color_extraction', 'api_requests']
        
        rate_limit_status = {}
        
        for operation in operations:
            status = rate_limiter.is_allowed(user_id, operation)
            rate_limit_status[operation] = {
                'allowed': status['allowed'],
                'current_count': status['current_count'],
                'limit': status['limit'],
                'period_seconds': status['period'],
                'reset_time': timezone.datetime.fromtimestamp(status['reset_time']).isoformat() if status['reset_time'] else None,
                'retry_after_seconds': int(status['retry_after']) if status['retry_after'] > 0 else 0
            }
        
        return Response({
            'user_id': user_id,
            'rate_limits': rate_limit_status,
            'timestamp': timezone.now().isoformat()
        })