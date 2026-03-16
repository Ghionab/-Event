"""
Secure API views for theme operations with comprehensive security measures.

These views integrate the enhanced security framework including:
- Secure image processing with malicious content scanning
- CSS injection prevention with whitelist validation
- Content Security Policy header generation
- Comprehensive audit logging
"""

import os
import json
import logging
import tempfile
from typing import Dict, Any
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from events.models import Event
from .models import EventTheme, ColorPalette, ThemeGenerationLog
from .serializers import (
    EventThemeSerializer, ColorExtractionRequestSerializer, 
    ColorExtractionResponseSerializer
)
from .permissions import IsEventOwnerOrReadOnly, CanModifyTheme
from .services.color_extractor import ColorExtractor
from .services.theme_generator import ThemeGenerator
from .security import (
    api_security_manager, 
    security_validator, 
    image_processor,
    audit_logger,
    permission_manager
)

logger = logging.getLogger(__name__)


class SecureColorExtractionAPIView(APIView):
    """
    Secure color extraction API with comprehensive security measures.
    
    Features:
    - Secure image processing with malicious content scanning
    - File format validation and size limits
    - Metadata stripping and path traversal prevention
    - Sandboxed image processing
    - Comprehensive audit logging
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated, CanModifyTheme]
    
    def post(self, request, event_id):
        """Extract colors from uploaded brand asset with security validation."""
        event = get_object_or_404(Event, id=event_id)
        
        # 1. Permission validation using enhanced permission manager
        permission_result = permission_manager.check_permission(
            request.user, 'extract_colors', event=event
        )
        
        if not permission_result['allowed']:
            audit_logger.log_security_event(
                'permission_denied',
                request.user,
                request,
                event_id=event_id,
                operation='color_extraction',
                reason=permission_result['reason']
            )
            return Response(
                {'error': permission_result['reason']},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 2. API security validation
        security_validation = api_security_manager.validate_api_request(
            request, 'color_extraction'
        )
        
        if not security_validation['is_valid']:
            audit_logger.log_security_event(
                'security_violation',
                request.user,
                request,
                event_id=event_id,
                errors=security_validation['errors'],
                security_level=security_validation['security_level']
            )
            return Response(
                {'error': 'Request blocked for security reasons'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 3. Validate uploaded file
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['image']
        
        try:
            with tempfile.TemporaryDirectory(prefix='secure_extraction_') as temp_dir:
                # Save uploaded file to secure temporary location
                temp_input_path = os.path.join(temp_dir, 'input_image')
                
                with open(temp_input_path, 'wb') as temp_file:
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)
                
                # 4. Comprehensive image security validation
                validation_result = image_processor.validate_image_file(temp_input_path)
                
                if not validation_result['is_valid']:
                    audit_logger.log_security_event(
                        'malicious_file_upload',
                        request.user,
                        request,
                        event_id=event_id,
                        filename=uploaded_file.name,
                        errors=validation_result['errors'],
                        security_scan=validation_result['security_scan']
                    )
                    return Response(
                        {
                            'error': 'File validation failed',
                            'details': validation_result['errors']
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Log security warnings if any
                if validation_result['warnings']:
                    audit_logger.log_security_event(
                        'file_security_warning',
                        request.user,
                        request,
                        event_id=event_id,
                        filename=uploaded_file.name,
                        warnings=validation_result['warnings'],
                        security_scan=validation_result['security_scan']
                    )
                
                # 5. Sanitize image in sandboxed environment
                temp_sanitized_path = os.path.join(temp_dir, 'sanitized_image.jpg')
                sanitization_result = image_processor.process_image_in_sandbox(
                    temp_input_path, temp_sanitized_path
                )
                
                if not sanitization_result['success']:
                    audit_logger.log_security_event(
                        'image_sanitization_failed',
                        request.user,
                        request,
                        event_id=event_id,
                        filename=uploaded_file.name,
                        warnings=sanitization_result['warnings']
                    )
                    return Response(
                        {'error': 'Image processing failed'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # 6. Extract colors from sanitized image
                color_extractor = ColorExtractor()
                extraction_result = color_extractor.extract_colors(
                    temp_sanitized_path,
                    algorithm=request.data.get('algorithm', 'kmeans')
                )
                
                # 7. Create or update color palette
                palette, created = ColorPalette.objects.get_or_create(
                    theme__event=event,
                    defaults={
                        'extracted_colors': [
                            {
                                'color': color.color,
                                'confidence': color.confidence,
                                'frequency': color.frequency,
                                'name': color.name
                            }
                            for color in extraction_result.colors
                        ],
                        'source_image': uploaded_file.name,
                        'extraction_algorithm': extraction_result.algorithm_used,
                        'extraction_parameters': {
                            'num_colors': len(extraction_result.colors),
                            'processing_time_ms': extraction_result.processing_time_ms
                        },
                        'color_diversity_score': extraction_result.diversity_score,
                        'overall_confidence': extraction_result.confidence_score
                    }
                )
                
                if not created:
                    # Update existing palette
                    palette.extracted_colors = [
                        {
                            'color': color.color,
                            'confidence': color.confidence,
                            'frequency': color.frequency,
                            'name': color.name
                        }
                        for color in extraction_result.colors
                    ]
                    palette.source_image = uploaded_file.name
                    palette.extraction_algorithm = extraction_result.algorithm_used
                    palette.color_diversity_score = extraction_result.diversity_score
                    palette.overall_confidence = extraction_result.confidence_score
                    palette.save()
                
                # 8. Log successful extraction
                audit_logger.log_security_event(
                    'color_extraction_success',
                    request.user,
                    request,
                    event_id=event_id,
                    filename=uploaded_file.name,
                    colors_extracted=len(extraction_result.colors),
                    confidence_score=extraction_result.confidence_score,
                    processing_time_ms=extraction_result.processing_time_ms,
                    security_measures=sanitization_result['security_measures']
                )
                
                # 9. Prepare response
                response_data = {
                    'success': True,
                    'extracted_colors': [
                        {
                            'color': color.color,
                            'rgb': color.rgb,
                            'confidence': color.confidence,
                            'frequency': color.frequency,
                            'name': color.name
                        }
                        for color in extraction_result.colors
                    ],
                    'image_properties': {
                        'width': extraction_result.image_properties.width,
                        'height': extraction_result.image_properties.height,
                        'format': extraction_result.image_properties.format,
                        'has_transparency': extraction_result.image_properties.has_transparency
                    },
                    'processing_metadata': {
                        'algorithm_used': extraction_result.algorithm_used,
                        'processing_time_ms': extraction_result.processing_time_ms,
                        'confidence_score': extraction_result.confidence_score,
                        'diversity_score': extraction_result.diversity_score,
                        'security_measures_applied': len(sanitization_result['security_measures'])
                    }
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Secure color extraction failed for event {event_id}: {str(e)}")
            
            audit_logger.log_security_event(
                'color_extraction_error',
                request.user,
                request,
                event_id=event_id,
                error_message=str(e)
            )
            
            return Response(
                {'error': f'Color extraction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SecureThemeValidationAPIView(APIView):
    """
    Secure theme validation API with comprehensive CSS security checks.
    
    Features:
    - CSS injection prevention with whitelist validation
    - Dangerous pattern detection and sanitization
    - Content Security Policy header generation
    - Accessibility compliance validation
    """
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrReadOnly]
    
    def post(self, request, event_id):
        """Validate theme colors and CSS with comprehensive security checks."""
        event = get_object_or_404(Event, id=event_id)
        
        # 1. Permission validation
        permission_result = permission_manager.check_permission(
            request.user, 'modify_theme', event=event
        )
        
        if not permission_result['allowed']:
            audit_logger.log_security_event(
                'permission_denied',
                request.user,
                request,
                event_id=event_id,
                operation='theme_validation',
                reason=permission_result['reason']
            )
            return Response(
                {'error': permission_result['reason']},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 2. API security validation
        security_validation = api_security_manager.validate_api_request(
            request, 'theme_validation'
        )
        
        if not security_validation['is_valid']:
            return Response(
                {'error': 'Request blocked for security reasons'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # 3. Extract validation data
            colors = request.data.get('colors', {})
            css_content = request.data.get('css_content', '')
            
            validation_results = {
                'colors': {},
                'css': {},
                'accessibility': {},
                'security': {},
                'csp_headers': {},
                'overall_valid': True,
                'security_score': 100
            }
            
            # 4. Validate colors with security checks
            for color_name, color_value in colors.items():
                is_valid = security_validator.validate_color_value(color_value)
                validation_results['colors'][color_name] = {
                    'value': color_value,
                    'valid': is_valid,
                    'security_checked': True
                }
                if not is_valid:
                    validation_results['overall_valid'] = False
                    validation_results['security_score'] -= 10
            
            # 5. Comprehensive CSS security validation
            if css_content:
                css_validation = security_validator.validate_css_content(css_content)
                validation_results['css'] = css_validation
                
                if not css_validation['is_valid']:
                    validation_results['overall_valid'] = False
                    validation_results['security_score'] -= 30
                
                # Generate CSP headers for the CSS
                csp_headers = security_validator.generate_csp_headers(css_content)
                validation_results['csp_headers'] = csp_headers
                
                # Log CSS security analysis
                if css_validation['security_analysis']['dangerous_patterns_found']:
                    audit_logger.log_security_event(
                        'css_security_violation',
                        request.user,
                        request,
                        event_id=event_id,
                        dangerous_patterns=css_validation['security_analysis']['dangerous_patterns_found'],
                        csp_violations=css_validation['csp_violations']
                    )
            
            # 6. Accessibility validation
            if colors:
                theme_generator = ThemeGenerator()
                try:
                    # Use the existing accessibility check from theme generator
                    accessibility_compliant, adjustments_made = theme_generator._check_accessibility_compliance(colors)
                    validation_results['accessibility'] = {
                        'wcag_compliant': accessibility_compliant,
                        'adjustments_needed': adjustments_made,
                        'contrast_ratios': {}  # Would be populated by detailed accessibility check
                    }
                    if not accessibility_compliant:
                        validation_results['security_score'] -= 20
                except Exception as e:
                    logger.warning(f"Accessibility validation failed: {str(e)}")
                    validation_results['accessibility'] = {
                        'wcag_compliant': False,
                        'error': str(e)
                    }
                    validation_results['security_score'] -= 20
            
            # 7. Overall security assessment
            validation_results['security'] = {
                'security_score': validation_results['security_score'],
                'security_level': 'high' if validation_results['security_score'] >= 80 else 
                                'medium' if validation_results['security_score'] >= 60 else 'low',
                'recommendations': []
            }
            
            # Add security recommendations
            if validation_results['security_score'] < 80:
                validation_results['security']['recommendations'].append(
                    'Review and fix security issues before applying theme'
                )
            
            if css_content and css_validation.get('warnings'):
                validation_results['security']['recommendations'].append(
                    'Consider simplifying CSS to reduce security warnings'
                )
            
            # 8. Log validation results
            audit_logger.log_security_event(
                'theme_validation_completed',
                request.user,
                request,
                event_id=event_id,
                security_score=validation_results['security_score'],
                overall_valid=validation_results['overall_valid'],
                colors_validated=len(colors),
                css_validated=bool(css_content)
            )
            
            return Response(validation_results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Secure theme validation failed for event {event_id}: {str(e)}")
            
            audit_logger.log_security_event(
                'theme_validation_error',
                request.user,
                request,
                event_id=event_id,
                error_message=str(e)
            )
            
            return Response(
                {'error': f'Validation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SecureThemeGenerationAPIView(APIView):
    """
    Secure theme generation API with comprehensive security measures.
    
    Features:
    - Secure CSS generation with sanitization
    - Content Security Policy header generation
    - Comprehensive audit logging
    - Rate limiting and permission validation
    """
    permission_classes = [permissions.IsAuthenticated, CanModifyTheme]
    
    def post(self, request, event_id):
        """Generate theme with comprehensive security measures."""
        event = get_object_or_404(Event, id=event_id)
        
        # 1. Permission validation
        permission_result = permission_manager.check_permission(
            request.user, 'create_theme', event=event
        )
        
        if not permission_result['allowed']:
            audit_logger.log_security_event(
                'permission_denied',
                request.user,
                request,
                event_id=event_id,
                operation='theme_generation',
                reason=permission_result['reason']
            )
            return Response(
                {'error': permission_result['reason']},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 2. API security validation
        security_validation = api_security_manager.validate_api_request(
            request, 'theme_generation'
        )
        
        if not security_validation['is_valid']:
            return Response(
                {'error': 'Request blocked for security reasons'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            with transaction.atomic():
                # 3. Extract and validate colors
                colors = request.data.get('colors', {})
                
                # Validate all colors for security
                for color_name, color_value in colors.items():
                    if not security_validator.validate_color_value(color_value):
                        audit_logger.log_security_event(
                            'invalid_color_value',
                            request.user,
                            request,
                            event_id=event_id,
                            color_name=color_name,
                            color_value=color_value
                        )
                        return Response(
                            {'error': f'Invalid color value for {color_name}: {color_value}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # 4. Generate theme with security measures
                theme_generator = ThemeGenerator()
                generated_theme = theme_generator.generate_theme(colors)
                
                # 5. Validate generated CSS for security
                css_validation = security_validator.validate_css_content(generated_theme.css_content)
                
                if not css_validation['is_valid']:
                    audit_logger.log_security_event(
                        'generated_css_security_violation',
                        request.user,
                        request,
                        event_id=event_id,
                        errors=css_validation['errors'],
                        dangerous_patterns=css_validation['security_analysis']['dangerous_patterns_found']
                    )
                    return Response(
                        {'error': 'Generated CSS failed security validation'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Use sanitized CSS
                sanitized_css = css_validation['sanitized_css']
                
                # 6. Create or update theme
                theme, created = EventTheme.objects.get_or_create(
                    event=event,
                    defaults={
                        'primary_color': colors.get('primary_color', '#007bff'),
                        'secondary_color': colors.get('secondary_color', '#6c757d'),
                        'accent_color': colors.get('accent_color', '#28a745'),
                        'neutral_light': colors.get('neutral_light', '#f8f9fa'),
                        'neutral_dark': colors.get('neutral_dark', '#343a40'),
                        'css_content': sanitized_css,
                        'generation_method': 'secure_api',
                        'wcag_compliant': generated_theme.accessibility_compliant,
                        'contrast_adjustments_made': generated_theme.contrast_adjustments_made,
                    }
                )
                
                if not created:
                    # Update existing theme
                    theme.primary_color = colors.get('primary_color', theme.primary_color)
                    theme.secondary_color = colors.get('secondary_color', theme.secondary_color)
                    theme.accent_color = colors.get('accent_color', theme.accent_color)
                    theme.neutral_light = colors.get('neutral_light', theme.neutral_light)
                    theme.neutral_dark = colors.get('neutral_dark', theme.neutral_dark)
                    theme.css_content = sanitized_css
                    theme.generation_method = 'secure_api'
                    theme.wcag_compliant = generated_theme.accessibility_compliant
                    theme.contrast_adjustments_made = generated_theme.contrast_adjustments_made
                    theme.save()
                
                # 7. Generate CSP headers for the theme
                csp_headers = security_validator.generate_csp_headers(sanitized_css)
                
                # 8. Log successful generation
                audit_logger.log_security_event(
                    'secure_theme_generation_success',
                    request.user,
                    request,
                    event_id=event_id,
                    theme_id=theme.id,
                    colors_used=len(colors),
                    css_sanitized=sanitized_css != generated_theme.css_content,
                    accessibility_compliant=generated_theme.accessibility_compliant
                )
                
                # 9. Prepare secure response
                response_data = {
                    'success': True,
                    'theme': {
                        'id': theme.id,
                        'primary_color': theme.primary_color,
                        'secondary_color': theme.secondary_color,
                        'accent_color': theme.accent_color,
                        'neutral_light': theme.neutral_light,
                        'neutral_dark': theme.neutral_dark,
                        'wcag_compliant': theme.wcag_compliant,
                        'contrast_adjustments_made': theme.contrast_adjustments_made,
                        'generation_method': theme.generation_method
                    },
                    'security': {
                        'css_sanitized': sanitized_css != generated_theme.css_content,
                        'csp_headers': csp_headers,
                        'security_warnings': css_validation['warnings']
                    }
                }
                
                # Add CSP headers to response
                response = Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                for header_name, header_value in csp_headers.items():
                    response[header_name] = header_value
                
                return response
                
        except Exception as e:
            logger.error(f"Secure theme generation failed for event {event_id}: {str(e)}")
            
            audit_logger.log_security_event(
                'theme_generation_error',
                request.user,
                request,
                event_id=event_id,
                error_message=str(e)
            )
            
            return Response(
                {'error': f'Theme generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )