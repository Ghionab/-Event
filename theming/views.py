from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from events.models import Event
from .models import EventTheme, ColorPalette, ThemeVariation, ThemeCache, ThemeGenerationLog
from .services.portal_renderer import PortalRenderer
from .services.color_extractor import ColorExtractor
from .services.theme_generator import ThemeGenerator
import json


class ThemeListView(LoginRequiredMixin, ListView):
    """List all themes for events the user has access to"""
    model = EventTheme
    template_name = 'theming/theme_list.html'
    context_object_name = 'themes'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter themes based on user's events
        user_events = Event.objects.filter(organizer=self.request.user)
        return EventTheme.objects.filter(event__in=user_events).select_related('event')


class EventThemeDetailView(LoginRequiredMixin, DetailView):
    """Display theme details for a specific event"""
    model = EventTheme
    template_name = 'theming/event_theme_detail.html'
    context_object_name = 'theme'
    
    def get_object(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, id=event_id, organizer=self.request.user)
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
        return theme
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['variations'] = self.object.variations.filter(is_active=True)
        context['logs'] = self.object.event.theme_logs.all()[:10]
        return context


class GenerateThemeView(LoginRequiredMixin, View):
    """Generate or regenerate theme for an event"""
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        
        # Log the generation attempt
        log_entry = ThemeGenerationLog.log_operation(
            event=event,
            operation_type='generation',
            status='success',  # We'll update this based on actual result
            user=request.user,
            processing_time_ms=100,  # Placeholder
            extraction_confidence=0.8,  # Placeholder
        )
        
        try:
            # Initialize services
            color_extractor = ColorExtractor()
            theme_generator = ThemeGenerator()
            
            # For now, create a basic theme (actual color extraction would happen here)
            # In a real implementation, this would extract colors from uploaded brand assets
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
            
            messages.success(request, f'Theme generated successfully for {event.title}')
            return JsonResponse({
                'success': True,
                'message': 'Theme generated successfully',
                'theme_id': theme.id,
                'redirect_url': reverse('theming:event_theme', kwargs={'event_id': event_id})
            })
            
        except Exception as e:
            log_entry.status = 'failure'
            log_entry.error_message = str(e)
            log_entry.save()
            
            return JsonResponse({
                'success': False,
                'message': f'Theme generation failed: {str(e)}'
            }, status=500)
    
    def _generate_basic_css(self):
        """Generate basic CSS theme (placeholder implementation)"""
        return """
        :root {
            --theme-primary: #007bff;
            --theme-secondary: #6c757d;
            --theme-accent: #28a745;
            --theme-neutral-light: #f8f9fa;
            --theme-neutral-dark: #343a40;
            
            /* Interactive states */
            --theme-hover: #0056b3;
            --theme-active: #004085;
            --theme-focus: rgba(0, 123, 255, 0.25);
        }
        
        /* Apply theme colors to common elements */
        .btn-primary {
            background-color: var(--theme-primary);
            border-color: var(--theme-primary);
        }
        
        .btn-primary:hover {
            background-color: var(--theme-hover);
            border-color: var(--theme-hover);
        }
        
        .navbar-brand {
            color: var(--theme-primary) !important;
        }
        
        .card-header {
            background-color: var(--theme-neutral-light);
            border-bottom: 1px solid var(--theme-primary);
        }
        """


class ThemePreviewView(LoginRequiredMixin, View):
    """Preview theme for a specific portal"""
    
    def get(self, request, event_id, portal_type):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        
        try:
            renderer = PortalRenderer()
            theme = renderer.get_theme_for_event(event_id)
            
            if not theme:
                return JsonResponse({'error': 'Theme not found'}, status=404)
            
            # Generate portal-specific CSS
            css_content = renderer.generate_portal_css(theme, portal_type)
            
            # Validate compatibility
            is_compatible = renderer.validate_portal_compatibility(theme, portal_type)
            
            return HttpResponse(css_content, content_type='text/css', headers={
                'X-Theme-Compatible': str(is_compatible).lower(),
                'X-Theme-ID': str(theme.id),
                'X-Portal-Type': portal_type,
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _generate_portal_css(self, theme, portal_type):
        """Generate portal-specific CSS"""
        base_css = theme.css_content
        
        # Add portal-specific customizations
        portal_customizations = {
            'staff': """
                /* Staff portal customizations */
                .staff-header { background-color: var(--theme-primary); }
                .staff-sidebar { border-left: 3px solid var(--theme-accent); }
            """,
            'participant': """
                /* Participant portal customizations */
                .participant-nav { background: linear-gradient(135deg, var(--theme-primary), var(--theme-accent)); }
                .event-card { border-top: 4px solid var(--theme-primary); }
            """,
            'organizer': """
                /* Organizer portal customizations */
                .organizer-dashboard { background-color: var(--theme-neutral-light); }
                .metric-card { border-left: 4px solid var(--theme-primary); }
            """
        }
        
        return base_css + portal_customizations.get(portal_type, '')


class ExtractColorsView(LoginRequiredMixin, View):
    """Extract colors from uploaded brand assets"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_id):
        from .services.color_extractor import ColorExtractor
        import tempfile
        import os
        
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        
        # Check if image was uploaded
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)
        
        uploaded_file = request.FILES['image']
        
        # Validate file size (10MB limit as per requirements)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'Image file too large (max 10MB)'}, status=400)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # Extract colors using ColorExtractor
            extractor = ColorExtractor(num_colors=5)
            algorithm = request.POST.get('algorithm', 'kmeans')
            
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
            from .models import ThemeGenerationLog
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
            
            return JsonResponse({
                'success': True,
                'extracted_colors': extracted_colors,
                'overall_confidence': result.confidence_score,
                'diversity_score': result.diversity_score,
                'processing_time_ms': result.processing_time_ms,
                'algorithm_used': result.algorithm_used,
                'image_properties': {
                    'width': result.image_properties.width,
                    'height': result.image_properties.height,
                    'format': result.image_properties.format,
                    'has_transparency': result.image_properties.has_transparency
                }
            })
            
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
            return JsonResponse({'error': str(e)}, status=400)
            
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
            return JsonResponse({'error': f'Color extraction failed: {str(e)}'}, status=500)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class ColorPaletteView(LoginRequiredMixin, View):
    """Get color palette for an event"""
    
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        
        try:
            theme = EventTheme.objects.get(event=event)
            palette = theme.palette
            return JsonResponse({
                'extracted_colors': palette.extracted_colors,
                'overall_confidence': palette.overall_confidence,
                'color_diversity_score': palette.color_diversity_score,
                'extraction_algorithm': palette.extraction_algorithm,
            })
        except (EventTheme.DoesNotExist, ColorPalette.DoesNotExist):
            return JsonResponse({'error': 'Color palette not found'}, status=404)


class ThemeVariationListView(LoginRequiredMixin, ListView):
    """List theme variations for an event"""
    model = ThemeVariation
    template_name = 'theming/theme_variations.html'
    context_object_name = 'variations'
    
    def get_queryset(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, id=event_id, organizer=self.request.user)
        theme = get_object_or_404(EventTheme, event=event)
        return theme.variations.all()


class CreateThemeVariationView(LoginRequiredMixin, View):
    """Create a new theme variation"""
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        theme = get_object_or_404(EventTheme, event=event)
        
        variation_type = request.POST.get('variation_type', 'light')
        
        # Generate variation CSS (placeholder)
        variation_css = theme.css_content + f"\n/* {variation_type} variation */"
        
        variation = ThemeVariation.objects.create(
            base_theme=theme,
            variation_type=variation_type,
            css_content=variation_css,
        )
        
        return JsonResponse({
            'success': True,
            'variation_id': variation.id,
            'variation_type': variation.get_variation_type_display(),
        })


class ClearThemeCacheView(LoginRequiredMixin, View):
    """Clear theme cache for an event"""
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        theme = get_object_or_404(EventTheme, event=event)
        
        # Clear all cache entries for this theme
        deleted_count = theme.cache_entries.all().delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Cleared {deleted_count} cache entries',
        })


class CacheStatsView(LoginRequiredMixin, View):
    """Get cache performance statistics"""
    
    def get(self, request):
        stats = {
            'total_entries': ThemeCache.objects.count(),
            'expired_entries': ThemeCache.objects.filter(expires_at__lt=timezone.now()).count(),
            'total_access_count': sum(ThemeCache.objects.values_list('access_count', flat=True)),
            'portal_breakdown': {},
        }
        
        # Portal type breakdown
        for portal_type, _ in ThemeCache.PORTAL_TYPES:
            count = ThemeCache.objects.filter(portal_type=portal_type).count()
            stats['portal_breakdown'][portal_type] = count
        
        return JsonResponse(stats)


# API Views
class ThemeAPIView(APIView):
    """API endpoint for theme operations"""
    
    def get(self, request):
        """List all themes for the authenticated user"""
        user_events = Event.objects.filter(organizer=request.user)
        themes = EventTheme.objects.filter(event__in=user_events).select_related('event')
        
        data = []
        for theme in themes:
            data.append({
                'id': theme.id,
                'event_id': theme.event.id,
                'event_title': theme.event.title,
                'primary_color': theme.primary_color,
                'secondary_color': theme.secondary_color,
                'accent_color': theme.accent_color,
                'generation_method': theme.generation_method,
                'extraction_confidence': theme.extraction_confidence,
                'wcag_compliant': theme.wcag_compliant,
                'created_at': theme.created_at,
            })
        
        return Response(data)


class ThemeDetailAPIView(APIView):
    """API endpoint for individual theme operations"""
    
    def get(self, request, event_id):
        """Get theme details for a specific event"""
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        
        try:
            theme = EventTheme.objects.get(event=event)
            data = {
                'id': theme.id,
                'event_id': theme.event.id,
                'primary_color': theme.primary_color,
                'secondary_color': theme.secondary_color,
                'accent_color': theme.accent_color,
                'neutral_light': theme.neutral_light,
                'neutral_dark': theme.neutral_dark,
                'css_content': theme.css_content,
                'generation_method': theme.generation_method,
                'extraction_confidence': theme.extraction_confidence,
                'wcag_compliant': theme.wcag_compliant,
                'is_fallback': theme.is_fallback,
                'created_at': theme.created_at,
                'updated_at': theme.updated_at,
            }
            return Response(data)
        except EventTheme.DoesNotExist:
            return Response({'error': 'Theme not found'}, status=status.HTTP_404_NOT_FOUND)


class ExtractColorsAPIView(APIView):
    """API endpoint for color extraction"""
    
    def post(self, request):
        """Extract colors from uploaded image"""
        if 'image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mock color extraction response
        extracted_colors = [
            {"color": "#1e3a8a", "confidence": 0.95, "frequency": 0.35, "name": "Deep Blue"},
            {"color": "#3b82f6", "confidence": 0.88, "frequency": 0.28, "name": "Blue"},
            {"color": "#60a5fa", "confidence": 0.75, "frequency": 0.15, "name": "Light Blue"},
        ]
        
        return Response({
            'extracted_colors': extracted_colors,
            'overall_confidence': 0.85,
            'processing_time_ms': 120,
            'source_image': request.FILES['image'].name,
        })