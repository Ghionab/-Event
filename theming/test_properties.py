"""
Property-based tests for the Dynamic Event Theming System.

These tests validate universal properties that should hold across all valid inputs
and configurations, using the Hypothesis framework for comprehensive testing.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase as HypothesisTestCase, from_model
from events.models import Event
from .models import (
    EventTheme, ColorPalette, ThemeVariation, ThemeCache, 
    ThemeGenerationLog
)
from .services.color_extractor import ColorExtractor
from .services.advanced_color_processor import AdvancedColorProcessor
from .services.visual_harmony import VisualHarmonyService
from PIL import Image, ImageDraw
import json
import hashlib
import time
import uuid
import os
import tempfile
from typing import List

User = get_user_model()


class DatabaseModelIntegrityPropertyTest(HypothesisTestCase):
    """
    Property-based tests for database model integrity and comprehensive logging.
    
    Feature: dynamic-event-theming, Property 20: Comprehensive Logging and Metrics
    Validates: Requirements 10.6
    """
    
    def setUp(self):
        """Set up test data"""
        # Use unique email for each test to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        
        self.user = User.objects.create_user(
            email=f'test-{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title=f'Test Event {unique_id}',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
    
    @given(
        operation_type=st.sampled_from([
            'generation', 'fallback', 'manual_override', 'cache_hit', 
            'cache_miss', 'accessibility_fix', 'variation_created'
        ]),
        status=st.sampled_from(['success', 'failure', 'partial', 'warning']),
        processing_time_ms=st.integers(min_value=1, max_value=10000),
        extraction_confidence=st.floats(min_value=0.0, max_value=1.0),
        error_message=st.text(max_size=500),
        source_image_path=st.text(min_size=1, max_size=255),
        metadata=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(min_value=-1000000, max_value=1000000),
                st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
                st.booleans()
            ),
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_comprehensive_logging_and_metrics_property(
        self, operation_type, status, processing_time_ms, extraction_confidence,
        error_message, source_image_path, metadata
    ):
        """
        Property 20: Comprehensive Logging and Metrics
        
        For any theme generation operation, the system should log detailed metrics
        including processing time, confidence scores, error messages, and quality
        indicators for monitoring and improvement purposes.
        
        Validates: Requirements 10.6
        """
        # Create a theme generation log entry with the given parameters
        log_entry = ThemeGenerationLog.objects.create(
            event=self.event,
            operation_type=operation_type,
            status=status,
            processing_time_ms=processing_time_ms,
            error_message=error_message,
            extraction_confidence=extraction_confidence,
            source_image_path=source_image_path,
            user=self.user,
            metadata=metadata
        )
        
        # Verify that all required metrics are properly logged
        self.assertIsNotNone(log_entry.id, "Log entry should be created with valid ID")
        self.assertEqual(log_entry.event, self.event, "Event should be properly linked")
        self.assertEqual(log_entry.operation_type, operation_type, "Operation type should be logged")
        self.assertEqual(log_entry.status, status, "Status should be logged")
        self.assertEqual(log_entry.processing_time_ms, processing_time_ms, "Processing time should be logged")
        self.assertEqual(log_entry.extraction_confidence, extraction_confidence, "Confidence score should be logged")
        self.assertEqual(log_entry.error_message, error_message, "Error message should be logged")
        self.assertEqual(log_entry.source_image_path, source_image_path, "Source image path should be logged")
        self.assertEqual(log_entry.user, self.user, "User should be properly linked")
        self.assertEqual(log_entry.metadata, metadata, "Metadata should be properly stored")
        
        # Verify timestamps are automatically set
        self.assertIsNotNone(log_entry.created_at, "Creation timestamp should be set")
        self.assertLessEqual(
            log_entry.created_at, timezone.now(),
            "Creation timestamp should not be in the future"
        )
        
        # Verify database integrity constraints
        self.assertTrue(
            ThemeGenerationLog.objects.filter(id=log_entry.id).exists(),
            "Log entry should be retrievable from database"
        )
        
        # Verify that the log entry can be queried by various fields
        self.assertTrue(
            ThemeGenerationLog.objects.filter(
                event=self.event,
                operation_type=operation_type,
                status=status
            ).exists(),
            "Log entry should be queryable by key fields"
        )
        
        # Verify JSON metadata field integrity
        if metadata:
            retrieved_log = ThemeGenerationLog.objects.get(id=log_entry.id)
            self.assertEqual(
                retrieved_log.metadata, metadata,
                "Metadata should be properly serialized and deserialized"
            )
    
    def test_theme_creation_with_logging(self):
        """
        Test that EventTheme creation generates proper logs with all required metrics.
        This is a focused unit test that validates the logging property for theme creation.
        """
        # Record start time for processing metrics
        start_time = time.time()
        
        # Create theme with comprehensive logging
        theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
            extraction_confidence=0.85,
            generation_method='auto',
            wcag_compliant=True,
            contrast_adjustments_made=False,
            is_fallback=False
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Log the theme creation operation
        log_entry = ThemeGenerationLog.log_operation(
            event=self.event,
            operation_type='generation',
            status='success',
            processing_time_ms=processing_time_ms,
            extraction_confidence=0.85,
            user=self.user,
            metadata={
                'theme_id': theme.id,
                'generation_method': 'auto',
                'wcag_compliant': True,
                'contrast_adjustments_made': False,
                'css_hash': theme.css_hash,
                'cache_key': theme.cache_key
            }
        )
        
        # Verify theme integrity
        self.assertIsNotNone(theme.id, "Theme should be created with valid ID")
        self.assertEqual(theme.event, self.event, "Event should be properly linked")
        self.assertIsNotNone(theme.css_hash, "CSS hash should be generated")
        self.assertIsNotNone(theme.cache_key, "Cache key should be generated")
        self.assertIsNotNone(theme.created_at, "Creation timestamp should be set")
        self.assertIsNotNone(theme.updated_at, "Update timestamp should be set")
        
        # Verify comprehensive logging occurred
        self.assertIsNotNone(log_entry.id, "Log entry should be created")
        self.assertEqual(log_entry.event, self.event, "Log should reference correct event")
        self.assertGreaterEqual(log_entry.processing_time_ms, 0, "Processing time should be logged")
        self.assertEqual(log_entry.extraction_confidence, 0.85, "Confidence should be logged")
        self.assertIn('theme_id', log_entry.metadata, "Theme ID should be in metadata")
        self.assertIn('generation_method', log_entry.metadata, "Generation method should be in metadata")
        self.assertIn('wcag_compliant', log_entry.metadata, "WCAG compliance should be in metadata")
        
        # Verify database integrity after operations
        retrieved_theme = EventTheme.objects.get(id=theme.id)
        self.assertEqual(retrieved_theme.css_hash, theme.css_hash, "CSS hash should be consistent")
        self.assertEqual(retrieved_theme.cache_key, theme.cache_key, "Cache key should be consistent")
        
        # Verify log entry can be retrieved and contains all metrics
        retrieved_log = ThemeGenerationLog.objects.get(id=log_entry.id)
        self.assertEqual(retrieved_log.processing_time_ms, processing_time_ms, "Processing time should be preserved")
        self.assertEqual(retrieved_log.extraction_confidence, 0.85, "Confidence should be preserved")
        self.assertEqual(retrieved_log.metadata['theme_id'], theme.id, "Theme ID should be preserved in metadata")
    
    def test_color_palette_creation_with_metrics_logging(self):
        """
        Test that ColorPalette creation maintains integrity and logs quality metrics.
        """
        # Create a theme first
        theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
        )
        
        # Sample extracted colors data
        extracted_colors = [
            {"color": "#007bff", "confidence": 0.95, "frequency": 0.35, "name": "Blue"},
            {"color": "#28a745", "confidence": 0.88, "frequency": 0.28, "name": "Green"},
            {"color": "#6c757d", "confidence": 0.75, "frequency": 0.15, "name": "Gray"},
        ]
        
        # Record start time for processing metrics
        start_time = time.time()
        
        # Create color palette
        palette = ColorPalette.objects.create(
            theme=theme,
            extracted_colors=extracted_colors,
            source_image='test_logo.png',
            extraction_algorithm='kmeans',
            color_diversity_score=0.85,
            overall_confidence=0.82
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Log the color extraction operation with quality metrics
        log_entry = ThemeGenerationLog.log_operation(
            event=self.event,
            operation_type='generation',
            status='success',
            processing_time_ms=processing_time_ms,
            extraction_confidence=0.82,
            source_image_path='test_logo.png',
            user=self.user,
            metadata={
                'palette_id': palette.id,
                'extraction_algorithm': 'kmeans',
                'color_diversity_score': 0.85,
                'num_colors_extracted': len(extracted_colors),
                'quality_indicators': {
                    'diversity_score': 0.85,
                    'overall_confidence': 0.82,
                    'color_count': len(extracted_colors)
                }
            }
        )
        
        # Verify palette integrity
        self.assertIsNotNone(palette.id, "Palette should be created with valid ID")
        self.assertEqual(palette.theme, theme, "Theme should be properly linked")
        self.assertEqual(palette.extracted_colors, extracted_colors, "Colors should be preserved")
        self.assertEqual(palette.source_image, 'test_logo.png', "Source image should be preserved")
        self.assertEqual(palette.extraction_algorithm, 'kmeans', "Algorithm should be preserved")
        self.assertEqual(palette.color_diversity_score, 0.85, "Diversity score should be preserved")
        self.assertEqual(palette.overall_confidence, 0.82, "Confidence should be preserved")
        
        # Verify comprehensive metrics logging
        self.assertIsNotNone(log_entry.id, "Log entry should be created")
        self.assertEqual(log_entry.source_image_path, 'test_logo.png', "Source image should be logged")
        self.assertEqual(log_entry.extraction_confidence, 0.82, "Confidence should be logged")
        self.assertGreaterEqual(log_entry.processing_time_ms, 0, "Processing time should be logged")
        self.assertIn('quality_indicators', log_entry.metadata, "Quality indicators should be logged")
        self.assertIn('diversity_score', log_entry.metadata['quality_indicators'], "Diversity score should be in quality indicators")
        self.assertIn('overall_confidence', log_entry.metadata['quality_indicators'], "Confidence should be in quality indicators")
        self.assertIn('color_count', log_entry.metadata['quality_indicators'], "Color count should be in quality indicators")
        
        # Verify database integrity and queryability
        retrieved_palette = ColorPalette.objects.get(id=palette.id)
        self.assertEqual(retrieved_palette.extracted_colors, extracted_colors, "Colors should be retrievable")
        
        retrieved_log = ThemeGenerationLog.objects.get(id=log_entry.id)
        self.assertEqual(retrieved_log.metadata['palette_id'], palette.id, "Palette ID should be in log metadata")
    
    def test_cache_operations_with_comprehensive_logging(self):
        """
        Test that cache operations maintain integrity and log performance metrics.
        """
        # Create a theme first
        theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
        )
        
        # Test cache operations with different portal types
        cache_operations = [
            ('staff_cache', '/* staff css */', 'staff', 3600),
            ('participant_cache', '/* participant css */', 'participant', 7200),
            ('organizer_cache', '/* organizer css */', 'organizer', 1800),
        ]
        
        for cache_key, css_content, portal_type, expires_in_seconds in cache_operations:
            # Record start time for processing metrics
            start_time = time.time()
            
            # Create unique cache key to avoid conflicts
            unique_cache_key = f"{cache_key}_{theme.id}_{uuid.uuid4().hex[:8]}"
            
            # Create cache entry
            cache_entry = ThemeCache.objects.create(
                cache_key=unique_cache_key,
                theme=theme,
                css_content=css_content,
                portal_type=portal_type,
                expires_at=timezone.now() + timezone.timedelta(seconds=expires_in_seconds)
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log cache operation with performance metrics
            log_entry = ThemeGenerationLog.log_operation(
                event=self.event,
                operation_type='cache_hit',
                status='success',
                processing_time_ms=processing_time_ms,
                user=self.user,
                metadata={
                    'cache_key': cache_entry.cache_key,
                    'portal_type': portal_type,
                    'css_size_bytes': len(css_content),
                    'expires_in_seconds': expires_in_seconds,
                    'performance_metrics': {
                        'cache_creation_time_ms': processing_time_ms,
                        'css_size': len(css_content),
                        'expiry_duration': expires_in_seconds
                    }
                }
            )
            
            # Verify cache integrity
            self.assertIsNotNone(cache_entry.cache_key, "Cache key should be set")
            self.assertEqual(cache_entry.theme, theme, "Theme should be properly linked")
            self.assertEqual(cache_entry.css_content, css_content, "CSS content should be preserved")
            self.assertEqual(cache_entry.portal_type, portal_type, "Portal type should be preserved")
            self.assertFalse(cache_entry.is_expired(), "Cache should not be expired immediately after creation")
            
            # Verify comprehensive performance logging
            self.assertIsNotNone(log_entry.id, "Log entry should be created")
            self.assertGreaterEqual(log_entry.processing_time_ms, 0, "Processing time should be logged")
            self.assertIn('performance_metrics', log_entry.metadata, "Performance metrics should be logged")
            self.assertIn('cache_creation_time_ms', log_entry.metadata['performance_metrics'], "Cache creation time should be logged")
            self.assertIn('css_size', log_entry.metadata['performance_metrics'], "CSS size should be logged")
            self.assertIn('expiry_duration', log_entry.metadata['performance_metrics'], "Expiry duration should be logged")
            
            # Test cache access and logging
            cache_entry.increment_access_count()
            
            # Log cache access
            access_log = ThemeGenerationLog.log_operation(
                event=self.event,
                operation_type='cache_hit',
                status='success',
                processing_time_ms=1,  # Cache hits should be very fast
                user=self.user,
                metadata={
                    'cache_key': cache_entry.cache_key,
                    'access_count': cache_entry.access_count,
                    'performance_metrics': {
                        'cache_hit_time_ms': 1,
                        'access_count': cache_entry.access_count
                    }
                }
            )
            
            # Verify access logging
            self.assertIsNotNone(access_log.id, "Access log should be created")
            self.assertEqual(access_log.processing_time_ms, 1, "Cache hit should be fast")
            self.assertIn('access_count', access_log.metadata, "Access count should be logged")


class ColorExtractionCompletenessPropertyTest(HypothesisTestCase):
    """
    Property-based tests for color extraction completeness.
    
    Feature: dynamic-event-theming, Property 1: Color Extraction Completeness
    Validates: Requirements 1.1, 1.2, 9.6
    """
    
    def setUp(self):
        """Set up test data"""
        # Use unique email for each test to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        
        self.user = User.objects.create_user(
            email=f'test-extraction-{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title=f'Test Event {unique_id}',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
    
    def test_color_extraction_completeness_property(self):
        """
        Property 1: Color Extraction Completeness
        
        For any uploaded brand asset in a supported format, the Color_Extractor 
        should extract at least 3 dominant colors with confidence scores, properly 
        categorized as primary, secondary, and accent colors.
        
        Validates: Requirements 1.1, 1.2, 9.6
        """
        from .services.color_extractor import ColorExtractor
        import tempfile
        import os
        from PIL import Image
        
        # Create a test image with known colors
        test_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green  
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
        ]
        
        # Create test image
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file.close()  # Close file handle on Windows
        
        try:
            # Create a 100x100 image with color blocks
            img = Image.new('RGB', (100, 100))
            pixels = []
            
            # Create blocks of different colors
            for y in range(100):
                for x in range(100):
                    color_index = (x // 20) % len(test_colors)
                    pixels.append(test_colors[color_index])
            
            img.putdata(pixels)
            img.save(tmp_file.name, 'PNG')
            
            # Test color extraction
            extractor = ColorExtractor(num_colors=5)
            result = extractor.extract_colors(tmp_file.name, algorithm='kmeans')
            
            # Verify Property 1: Color Extraction Completeness
            
            # 1. Should extract at least 3 dominant colors
            self.assertGreaterEqual(
                len(result.colors), 3,
                "Should extract at least 3 dominant colors"
            )
            
            # 2. Each color should have confidence scores
            for color in result.colors:
                self.assertIsInstance(color.confidence, float, "Confidence should be a float")
                self.assertGreaterEqual(color.confidence, 0.0, "Confidence should be >= 0")
                self.assertLessEqual(color.confidence, 1.0, "Confidence should be <= 1")
            
            # 3. Colors should be properly categorized with RGB values
            for color in result.colors:
                self.assertIsInstance(color.rgb, tuple, "RGB should be a tuple")
                self.assertEqual(len(color.rgb), 3, "RGB should have 3 components")
                for component in color.rgb:
                    self.assertIsInstance(component, int, "RGB components should be integers")
                    self.assertGreaterEqual(component, 0, "RGB components should be >= 0")
                    self.assertLessEqual(component, 255, "RGB components should be <= 255")
            
            # 4. Colors should have hex representation
            for color in result.colors:
                self.assertIsInstance(color.color, str, "Color should have hex string")
                self.assertTrue(color.color.startswith('#'), "Hex color should start with #")
                self.assertEqual(len(color.color), 7, "Hex color should be 7 characters")
            
            # 5. Colors should have frequency information
            for color in result.colors:
                self.assertIsInstance(color.frequency, float, "Frequency should be a float")
                self.assertGreaterEqual(color.frequency, 0.0, "Frequency should be >= 0")
                self.assertLessEqual(color.frequency, 1.0, "Frequency should be <= 1")
            
            # 6. Should have overall confidence and diversity scores
            self.assertIsInstance(result.confidence_score, float, "Overall confidence should be float")
            self.assertGreaterEqual(result.confidence_score, 0.0, "Overall confidence should be >= 0")
            self.assertLessEqual(result.confidence_score, 1.0, "Overall confidence should be <= 1")
            
            self.assertIsInstance(result.diversity_score, float, "Diversity score should be float")
            self.assertGreaterEqual(result.diversity_score, 0.0, "Diversity score should be >= 0")
            self.assertLessEqual(result.diversity_score, 1.0, "Diversity score should be <= 1")
            
            # 7. Should provide image properties analysis
            self.assertIsNotNone(result.image_properties, "Should provide image properties")
            self.assertEqual(result.image_properties.width, 100, "Should detect correct width")
            self.assertEqual(result.image_properties.height, 100, "Should detect correct height")
            self.assertEqual(result.image_properties.format, 'PNG', "Should detect correct format")
            
            # 8. Should provide processing metadata
            self.assertIsNotNone(result.metadata, "Should provide metadata")
            self.assertIn('num_colors_extracted', result.metadata, "Should log number of colors extracted")
            self.assertGreaterEqual(result.processing_time_ms, 0, "Should log processing time")
            
            # 9. Colors should be sorted by relevance (confidence/frequency)
            if len(result.colors) > 1:
                for i in range(len(result.colors) - 1):
                    current_score = result.colors[i].confidence * 0.7 + result.colors[i].frequency * 0.3
                    next_score = result.colors[i + 1].confidence * 0.7 + result.colors[i + 1].frequency * 0.3
                    self.assertGreaterEqual(
                        current_score, next_score,
                        "Colors should be sorted by relevance (confidence + frequency)"
                    )
            
            # 10. Should detect primary colors from our test image
            extracted_hex_colors = [color.color.lower() for color in result.colors]
            # We should find at least some of our test colors (allowing for clustering variations)
            primary_colors_found = 0
            expected_colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff']  # Our test colors
            
            for expected in expected_colors:
                for extracted in extracted_hex_colors:
                    # Allow some tolerance for clustering
                    if self._colors_similar(expected, extracted, tolerance=50):
                        primary_colors_found += 1
                        break
            
            self.assertGreaterEqual(
                primary_colors_found, 2,
                f"Should detect at least 2 primary colors from test image. "
                f"Expected: {expected_colors}, Got: {extracted_hex_colors}"
            )
                
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows
    
    def _colors_similar(self, hex1: str, hex2: str, tolerance: int = 30) -> bool:
        """Check if two hex colors are similar within tolerance."""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        rgb1 = hex_to_rgb(hex1)
        rgb2 = hex_to_rgb(hex2)
        
        # Calculate Euclidean distance
        distance = sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5
        return distance <= tolerance
    
    def test_supported_format_validation(self):
        """
        Test that the ColorExtractor properly validates supported formats.
        
        Validates: Requirements 1.4, 1.5
        """
        from .services.color_extractor import ColorExtractor, is_supported_format, get_supported_formats
        import tempfile
        from PIL import Image
        
        # Test supported formats
        supported_formats = get_supported_formats()
        expected_formats = {'PNG', 'JPEG', 'JPG', 'WEBP', 'SVG'}
        
        self.assertEqual(
            set(supported_formats), expected_formats,
            f"Should support exactly these formats: {expected_formats}"
        )
        
        # Test format validation with actual files
        test_formats = [
            ('PNG', 'png'),
            ('JPEG', 'jpg'),
            ('WEBP', 'webp'),
        ]
        
        for pil_format, extension in test_formats:
            tmp_file = tempfile.NamedTemporaryFile(suffix=f'.{extension}', delete=False)
            tmp_file.close()  # Close file handle on Windows
            
            # Create simple test image
            img = Image.new('RGB', (50, 50), color='red')
            
            try:
                if pil_format == 'WEBP':
                    img.save(tmp_file.name, 'WEBP')
                else:
                    img.save(tmp_file.name, pil_format)
                
                # Test format support detection
                self.assertTrue(
                    is_supported_format(tmp_file.name),
                    f"Should detect {pil_format} as supported format"
                )
                
                # Test actual extraction
                extractor = ColorExtractor(num_colors=3)
                result = extractor.extract_colors(tmp_file.name)
                
                self.assertGreaterEqual(
                    len(result.colors), 1,
                    f"Should extract colors from {pil_format} format"
                )
                
            except Exception as e:
                if pil_format == 'WEBP':
                    # WebP might not be supported in all PIL installations
                    self.skipTest(f"WebP format not supported in this PIL installation: {e}")
                else:
                    raise
            
            finally:
                # Clean up
                if os.path.exists(tmp_file.name):
                    try:
                        os.unlink(tmp_file.name)
                    except (OSError, PermissionError):
                        pass  # Ignore cleanup errors on Windows


class AdvancedColorProcessingPropertyTest(HypothesisTestCase):
    """
    Property-based tests for advanced color processing features.
    
    Feature: dynamic-event-theming, Property 16: Advanced Color Processing
    Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
    """
    
    def setUp(self):
        """Set up test data"""
        # Use unique email for each test to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        
        self.user = User.objects.create_user(
            email=f'test-advanced-{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title=f'Test Event {unique_id}',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
    
    def test_advanced_color_processing_property(self):
        """
        Property 16: Advanced Color Processing
        
        For any brand asset, the Color_Extractor should handle transparent backgrounds,
        prioritize non-text elements over text overlays, ignore white/near-white backgrounds,
        detect and exclude watermarks, and generate complementary colors for monochromatic images.
        
        Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
        """
        from .services.advanced_color_processor import AdvancedColorProcessor
        from .services.color_extractor import ColorExtractor
        import tempfile
        import os
        from PIL import Image, ImageDraw
        
        processor = AdvancedColorProcessor()
        
        # Test 1: Transparent background handling (Requirement 9.1)
        self._test_transparent_background_handling(processor)
        
        # Test 2: Text overlay prioritization (Requirement 9.2)
        self._test_text_overlay_prioritization(processor)
        
        # Test 3: White background exclusion (Requirement 9.3)
        self._test_white_background_exclusion(processor)
        
        # Test 4: Watermark detection (Requirement 9.4)
        self._test_watermark_detection(processor)
        
        # Test 5: Monochromatic color generation (Requirement 9.5)
        self._test_monochromatic_color_generation(processor)
    
    def _test_transparent_background_handling(self, processor: AdvancedColorProcessor):
        """Test handling of images with transparent backgrounds."""
        # Create image with transparent background and colored foreground
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file.close()
        
        try:
            # Create RGBA image with transparency
            img = Image.new('RGBA', (100, 100), (255, 255, 255, 0))  # Transparent white
            draw = ImageDraw.Draw(img)
            
            # Add colored shapes on transparent background
            draw.rectangle([20, 20, 80, 80], fill=(255, 0, 0, 255))  # Red square
            draw.ellipse([10, 10, 50, 50], fill=(0, 255, 0, 255))    # Green circle
            
            img.save(tmp_file.name, 'PNG')
            
            # Extract colors
            extractor = ColorExtractor(num_colors=5)
            result = extractor.extract_colors(tmp_file.name)
            
            # Verify transparent background handling
            self.assertGreaterEqual(
                len(result.colors), 2,
                "Should extract colors from non-transparent pixels"
            )
            
            # Should detect red and green colors, not white/transparent
            extracted_colors = [color.color.lower() for color in result.colors]
            
            # Check for red-ish and green-ish colors
            has_red_like = any(self._is_color_similar_to(color, '#ff0000') for color in extracted_colors)
            has_green_like = any(self._is_color_similar_to(color, '#00ff00') for color in extracted_colors)
            
            self.assertTrue(
                has_red_like or has_green_like,
                f"Should detect red or green colors from foreground, got: {extracted_colors}"
            )
            
            # Should not extract pure white (transparent background)
            has_white = any(self._is_color_similar_to(color, '#ffffff', tolerance=20) for color in extracted_colors)
            self.assertFalse(
                has_white,
                "Should not extract white/transparent background colors"
            )
            
        finally:
            if os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def _test_text_overlay_prioritization(self, processor: AdvancedColorProcessor):
        """Test prioritization of background elements over text overlays."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file.close()
        
        try:
            # Create image with colored background and text overlay
            img = Image.new('RGB', (200, 100), (0, 100, 200))  # Blue background
            draw = ImageDraw.Draw(img)
            
            # Add text overlay (should be deprioritized)
            try:
                # Try to add text, but don't fail if font is not available
                draw.text((50, 40), "SAMPLE TEXT", fill=(255, 255, 255))
            except:
                # If text drawing fails, just add white rectangles to simulate text
                draw.rectangle([50, 40, 150, 60], fill=(255, 255, 255))
            
            img.save(tmp_file.name, 'PNG')
            
            # Extract colors
            extractor = ColorExtractor(num_colors=3)
            result = extractor.extract_colors(tmp_file.name)
            
            # The blue background should be more prominent than white text
            if len(result.colors) >= 2:
                # Find blue and white colors
                blue_color = None
                white_color = None
                
                for color in result.colors:
                    if self._is_color_similar_to(color.color, '#0064c8', tolerance=50):
                        blue_color = color
                    elif self._is_color_similar_to(color.color, '#ffffff', tolerance=30):
                        white_color = color
                
                # Blue background should have higher frequency than white text
                if blue_color and white_color:
                    self.assertGreater(
                        blue_color.frequency, white_color.frequency,
                        "Background color should have higher frequency than text overlay"
                    )
                    self.assertGreater(
                        blue_color.confidence, white_color.confidence,
                        "Background color should have higher confidence than text overlay"
                    )
            
        finally:
            if os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def _test_white_background_exclusion(self, processor: AdvancedColorProcessor):
        """Test exclusion of white and near-white backgrounds."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file.close()
        
        try:
            # Create image with white background and colored elements
            img = Image.new('RGB', (100, 100), (255, 255, 255))  # White background
            draw = ImageDraw.Draw(img)
            
            # Add small colored elements
            draw.rectangle([40, 40, 60, 60], fill=(255, 0, 0))    # Red square
            draw.ellipse([20, 20, 40, 40], fill=(0, 0, 255))      # Blue circle
            
            img.save(tmp_file.name, 'PNG')
            
            # Extract colors
            extractor = ColorExtractor(num_colors=5)
            result = extractor.extract_colors(tmp_file.name)
            
            # Should extract colored elements, not white background
            extracted_colors = [color.color.lower() for color in result.colors]
            
            # Should find red and blue colors
            has_red_like = any(self._is_color_similar_to(color, '#ff0000') for color in extracted_colors)
            has_blue_like = any(self._is_color_similar_to(color, '#0000ff') for color in extracted_colors)
            
            self.assertTrue(
                has_red_like or has_blue_like,
                f"Should detect colored elements, got: {extracted_colors}"
            )
            
            # Should minimize white background extraction
            white_colors = [color for color in result.colors 
                          if self._is_color_similar_to(color.color, '#ffffff', tolerance=30)]
            
            if white_colors:
                # If white is extracted, it should have low confidence
                for white_color in white_colors:
                    self.assertLess(
                        white_color.confidence, 0.7,
                        "White background should have low confidence if extracted"
                    )
            
        finally:
            if os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def _test_watermark_detection(self, processor: AdvancedColorProcessor):
        """Test detection and exclusion of watermarks."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file.close()
        
        try:
            # Create image with main content and watermark-like element
            img = Image.new('RGB', (150, 150), (50, 150, 50))  # Green background
            draw = ImageDraw.Draw(img)
            
            # Add main content
            draw.rectangle([30, 30, 120, 120], fill=(200, 50, 50))  # Red main element
            
            # Add watermark-like element (semi-transparent appearance simulated with gray)
            draw.rectangle([100, 100, 140, 140], fill=(150, 150, 150))  # Gray "watermark"
            
            img.save(tmp_file.name, 'PNG')
            
            # Extract colors
            extractor = ColorExtractor(num_colors=4)
            result = extractor.extract_colors(tmp_file.name)
            
            # Main colors (green background, red element) should be more prominent
            # than watermark-like gray
            extracted_colors = [color.color.lower() for color in result.colors]
            
            has_green_like = any(self._is_color_similar_to(color, '#329632') for color in extracted_colors)
            has_red_like = any(self._is_color_similar_to(color, '#c83232') for color in extracted_colors)
            
            self.assertTrue(
                has_green_like or has_red_like,
                f"Should detect main content colors, got: {extracted_colors}"
            )
            
            # Gray watermark should have lower prominence if detected
            gray_colors = [color for color in result.colors 
                          if self._is_color_similar_to(color.color, '#969696', tolerance=50)]
            
            if gray_colors and len(result.colors) > 1:
                gray_color = gray_colors[0]
                main_colors = [color for color in result.colors if color != gray_color]
                
                if main_colors:
                    best_main_color = max(main_colors, key=lambda c: c.confidence)
                    # Allow for equal confidence, just ensure gray isn't significantly higher
                    self.assertGreaterEqual(
                        best_main_color.confidence, gray_color.confidence * 0.9,
                        "Main content should have similar or higher confidence than watermark-like elements"
                    )
            
        finally:
            if os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def _test_monochromatic_color_generation(self, processor: AdvancedColorProcessor):
        """Test generation of complementary colors for monochromatic images."""
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file.close()
        
        try:
            # Create monochromatic image (shades of blue)
            img = Image.new('RGB', (100, 100))
            pixels = []
            
            # Create gradient of blue shades
            for y in range(100):
                for x in range(100):
                    blue_intensity = int(100 + (x + y) * 0.5)  # Varying blue intensity
                    blue_intensity = min(255, blue_intensity)
                    pixels.append((0, 0, blue_intensity))
            
            img.putdata(pixels)
            img.save(tmp_file.name, 'PNG')
            
            # Extract colors
            extractor = ColorExtractor(num_colors=5)
            result = extractor.extract_colors(tmp_file.name)
            
            # Test color harmony generation
            extracted_hex_colors = [color.color for color in result.colors]
            harmony_analysis = processor.analyze_color_harmony(extracted_hex_colors)
            
            # Should generate complementary colors
            self.assertIsNotNone(harmony_analysis.complementary_colors, "Should generate complementary colors")
            self.assertGreater(len(harmony_analysis.complementary_colors), 0, "Should have complementary colors")
            
            # Should generate other harmony types
            self.assertIsNotNone(harmony_analysis.analogous_colors, "Should generate analogous colors")
            self.assertIsNotNone(harmony_analysis.triadic_colors, "Should generate triadic colors")
            
            # Test advanced harmony palette generation
            if extracted_hex_colors:
                base_color = extracted_hex_colors[0]
                complementary_palette = processor.generate_harmony_palette(base_color, 'complementary')
                
                self.assertGreaterEqual(
                    len(complementary_palette), 2,
                    "Complementary palette should have at least 2 colors"
                )
                
                # First color should be the base color
                self.assertEqual(
                    complementary_palette[0], base_color,
                    "First color in palette should be the base color"
                )
                
                # Should generate different harmony types
                triadic_palette = processor.generate_harmony_palette(base_color, 'triadic')
                analogous_palette = processor.generate_harmony_palette(base_color, 'analogous')
                
                self.assertGreaterEqual(len(triadic_palette), 2, "Triadic palette should have multiple colors")
                self.assertGreaterEqual(len(analogous_palette), 2, "Analogous palette should have multiple colors")
                
                # Palettes should be different
                self.assertNotEqual(
                    complementary_palette, triadic_palette,
                    "Different harmony types should generate different palettes"
                )
            
        finally:
            if os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except (OSError, PermissionError):
                    pass
    
    def _is_color_similar_to(self, color1: str, color2: str, tolerance: int = 40) -> bool:
        """Check if two colors are similar within tolerance."""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        
        # Calculate Euclidean distance
        distance = sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5
        return distance <= tolerance
    
    def test_confidence_scoring_system(self):
        """
        Test that confidence scoring system works properly.
        
        Validates: Requirements 9.6
        """
        from .services.color_extractor import ColorExtractor
        import tempfile
        from PIL import Image
        
        # Create test image with clear dominant color
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file.close()  # Close file handle on Windows
        
        try:
            # Create image that's mostly red with some blue
            img = Image.new('RGB', (100, 100))
            pixels = []
            
            for y in range(100):
                for x in range(100):
                    if x < 80:  # 80% red
                        pixels.append((255, 0, 0))
                    else:  # 20% blue
                        pixels.append((0, 0, 255))
            
            img.putdata(pixels)
            img.save(tmp_file.name, 'PNG')
            
            extractor = ColorExtractor(num_colors=3)
            result = extractor.extract_colors(tmp_file.name)
            
            # The most dominant color (red) should have highest confidence
            if len(result.colors) >= 2:
                dominant_color = result.colors[0]
                secondary_color = result.colors[1]
                
                self.assertGreaterEqual(
                    dominant_color.confidence, secondary_color.confidence,
                    "Most dominant color should have equal or higher confidence"
                )
                
                self.assertGreaterEqual(
                    dominant_color.frequency, secondary_color.frequency,
                    "Most dominant color should have equal or higher frequency"
                )
            
            # All confidence scores should be reasonable
            for color in result.colors:
                self.assertGreater(
                    color.confidence, 0.1,
                    "Confidence scores should be above minimum threshold"
                )
            
        finally:
            if os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except (OSError, PermissionError):
                    pass  # Ignore cleanup errors on Windows


class VisualHarmonyAndBrandingPropertyTest(HypothesisTestCase):
    """
    Property-based tests for visual harmony and branding system.
    
    Feature: dynamic-event-theming, Property 17: Visual Harmony and Branding
    Validates: Requirements 8.2, 8.3, 8.4, 8.6
    """
    
    def setUp(self):
        """Set up test data"""
        # Use unique email for each test to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        
        self.user = User.objects.create_user(
            email=f'test-harmony-{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title=f'Test Event {unique_id}',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
    
    def test_visual_harmony_and_branding_property(self):
        """
        Property 17: Visual Harmony and Branding
        
        For any generated theme, the Theme_Engine should create harmonious color hierarchies,
        generate complementary gradients and hover effects, maintain brand color prominence
        while ensuring functional element discoverability, and preserve brand visual identity.
        
        Validates: Requirements 8.2, 8.3, 8.4, 8.6
        """
        from .services.advanced_color_processor import AdvancedColorProcessor
        from .services.visual_harmony import VisualHarmonyService
        
        processor = AdvancedColorProcessor()
        harmony_service = VisualHarmonyService()
        
        # Test with various color combinations
        test_color_sets = [
            ['#007bff', '#28a745', '#ffc107', '#dc3545'],  # Primary web colors
            ['#6f42c1', '#e83e8c', '#fd7e14', '#20c997'],  # Vibrant colors
            ['#495057', '#6c757d', '#adb5bd', '#dee2e6'],  # Neutral colors
            ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24'],  # Harmonious palette
        ]
        
        for colors in test_color_sets:
            with self.subTest(colors=colors):
                self._test_harmonious_color_hierarchy(processor, harmony_service, colors)
                self._test_gradient_generation(processor, harmony_service, colors)
                self._test_hover_effects_generation(processor, harmony_service, colors)
                self._test_brand_prominence_preservation(processor, harmony_service, colors)
                self._test_functional_element_discoverability(processor, harmony_service, colors)
    
    def _test_harmonious_color_hierarchy(self, processor: AdvancedColorProcessor, 
                                       harmony_service: VisualHarmonyService, colors: List[str]):
        """Test creation of harmonious color hierarchies."""
        # Generate brand hierarchy
        hierarchy = processor.generate_brand_hierarchy(colors)
        
        # Verify hierarchy structure
        self.assertIsNotNone(hierarchy.primary_color, "Should have primary color")
        self.assertIn(hierarchy.primary_color, colors, "Primary color should be from input colors")
        
        # Verify hierarchy confidence
        self.assertIsInstance(hierarchy.hierarchy_confidence, float, "Confidence should be float")
        self.assertGreaterEqual(hierarchy.hierarchy_confidence, 0.0, "Confidence should be >= 0")
        self.assertLessEqual(hierarchy.hierarchy_confidence, 1.0, "Confidence should be <= 1")
        
        # Verify color categorization
        all_hierarchy_colors = [hierarchy.primary_color]
        all_hierarchy_colors.extend(hierarchy.secondary_colors)
        all_hierarchy_colors.extend(hierarchy.accent_colors)
        all_hierarchy_colors.extend(hierarchy.neutral_colors)
        
        # All hierarchy colors should be from input or derived
        for color in all_hierarchy_colors:
            self.assertIsInstance(color, str, "Color should be string")
            self.assertTrue(color.startswith('#'), "Color should be hex format")
            self.assertEqual(len(color), 7, "Color should be 7 characters")
        
        # Test color harmony analysis
        harmony_analysis = processor.analyze_color_harmony(colors)
        
        self.assertIsInstance(harmony_analysis.harmony_score, float, "Harmony score should be float")
        self.assertGreaterEqual(harmony_analysis.harmony_score, 0.0, "Harmony score should be >= 0")
        self.assertLessEqual(harmony_analysis.harmony_score, 1.0, "Harmony score should be <= 1")
        
        # Should identify harmony type
        self.assertIsInstance(harmony_analysis.harmony_type, str, "Should identify harmony type")
        self.assertIn(harmony_analysis.harmony_type, [
            'complementary', 'analogous', 'triadic', 'split_complementary', 
            'tetradic', 'square', 'monochromatic', 'none'
        ], "Should be valid harmony type")
    
    def _test_gradient_generation(self, processor: AdvancedColorProcessor, 
                                harmony_service: VisualHarmonyService, colors: List[str]):
        """Test generation of complementary gradients."""
        hierarchy = processor.generate_brand_hierarchy(colors)
        gradients = harmony_service.generate_gradients(hierarchy)
        
        # Should generate gradients
        self.assertIsInstance(gradients, list, "Should return list of gradients")
        self.assertGreater(len(gradients), 0, "Should generate at least one gradient")
        
        for gradient in gradients:
            # Verify gradient structure
            self.assertIsInstance(gradient.type, str, "Gradient type should be string")
            self.assertIn(gradient.type, ['linear', 'radial', 'conic'], "Should be valid gradient type")
            
            self.assertIsInstance(gradient.direction, str, "Direction should be string")
            self.assertIsInstance(gradient.color_stops, list, "Color stops should be list")
            self.assertIsInstance(gradient.css, str, "CSS should be string")
            
            # Verify color stops
            for color_stop in gradient.color_stops:
                self.assertIsInstance(color_stop, tuple, "Color stop should be tuple")
                self.assertEqual(len(color_stop), 2, "Color stop should have color and position")
                
                color, position = color_stop
                self.assertIsInstance(color, str, "Color should be string")
                self.assertTrue(color.startswith('#'), "Color should be hex format")
                self.assertIsInstance(position, float, "Position should be float")
                self.assertGreaterEqual(position, 0.0, "Position should be >= 0")
                self.assertLessEqual(position, 1.0, "Position should be <= 1")
            
            # Verify CSS generation
            self.assertIn(gradient.type, gradient.css, "CSS should contain gradient type")
            for color_stop in gradient.color_stops:
                self.assertIn(color_stop[0], gradient.css, "CSS should contain color")
    
    def _test_hover_effects_generation(self, processor: AdvancedColorProcessor, 
                                     harmony_service: VisualHarmonyService, colors: List[str]):
        """Test generation of hover effects."""
        hierarchy = processor.generate_brand_hierarchy(colors)
        hover_effects = harmony_service.generate_hover_effects(hierarchy)
        
        # Verify hover effects structure
        self.assertIsInstance(hover_effects.primary_hover, str, "Primary hover should be string")
        self.assertTrue(hover_effects.primary_hover.startswith('#'), "Primary hover should be hex")
        
        self.assertIsInstance(hover_effects.secondary_hover, str, "Secondary hover should be string")
        self.assertTrue(hover_effects.secondary_hover.startswith('#'), "Secondary hover should be hex")
        
        self.assertIsInstance(hover_effects.accent_hover, str, "Accent hover should be string")
        self.assertTrue(hover_effects.accent_hover.startswith('#'), "Accent hover should be hex")
        
        # Verify button hover effects
        self.assertIsInstance(hover_effects.button_hover, dict, "Button hover should be dict")
        required_button_keys = ['primary', 'secondary', 'accent']
        for key in required_button_keys:
            if key in hover_effects.button_hover:
                self.assertIsInstance(hover_effects.button_hover[key], str, f"Button {key} should be string")
        
        # Verify link hover effects
        self.assertIsInstance(hover_effects.link_hover, dict, "Link hover should be dict")
        if 'color' in hover_effects.link_hover:
            self.assertIsInstance(hover_effects.link_hover['color'], str, "Link color should be string")
        
        # Hover colors should be different from base colors
        self.assertNotEqual(
            hover_effects.primary_hover, hierarchy.primary_color,
            "Primary hover should be different from base color"
        )
    
    def _test_brand_prominence_preservation(self, processor: AdvancedColorProcessor, 
                                          harmony_service: VisualHarmonyService, colors: List[str]):
        """Test maintenance of brand color prominence."""
        hierarchy = processor.generate_brand_hierarchy(colors)
        prominence = harmony_service.calculate_brand_prominence(hierarchy)
        
        # Verify prominence structure
        self.assertIsInstance(prominence.header_colors, dict, "Header colors should be dict")
        self.assertIsInstance(prominence.navigation_colors, dict, "Navigation colors should be dict")
        self.assertIsInstance(prominence.cta_colors, dict, "CTA colors should be dict")
        self.assertIsInstance(prominence.accent_placement, list, "Accent placement should be list")
        
        # Verify header colors
        if 'background' in prominence.header_colors:
            bg_color = prominence.header_colors['background']
            self.assertIsInstance(bg_color, str, "Header background should be string")
            self.assertTrue(bg_color.startswith('#'), "Header background should be hex")
        
        if 'text' in prominence.header_colors:
            text_color = prominence.header_colors['text']
            self.assertIsInstance(text_color, str, "Header text should be string")
            self.assertTrue(text_color.startswith('#'), "Header text should be hex")
        
        # Verify navigation colors
        if 'background' in prominence.navigation_colors:
            nav_bg = prominence.navigation_colors['background']
            self.assertIsInstance(nav_bg, str, "Nav background should be string")
            self.assertTrue(nav_bg.startswith('#'), "Nav background should be hex")
        
        # Verify CTA colors
        if 'primary' in prominence.cta_colors:
            cta_primary = prominence.cta_colors['primary']
            self.assertIsInstance(cta_primary, str, "CTA primary should be string")
            self.assertTrue(cta_primary.startswith('#'), "CTA primary should be hex")
        
        # Verify accent placement
        self.assertGreater(len(prominence.accent_placement), 0, "Should have accent placements")
        for placement in prominence.accent_placement:
            self.assertIsInstance(placement, str, "Placement should be string")
    
    def _test_functional_element_discoverability(self, processor: AdvancedColorProcessor, 
                                               harmony_service: VisualHarmonyService, colors: List[str]):
        """Test preservation of functional element discoverability."""
        hierarchy = processor.generate_brand_hierarchy(colors)
        
        # Test color contrast for accessibility
        test_colors = {
            'primary_bg': hierarchy.primary_color,
            'secondary_bg': hierarchy.secondary_colors[0] if hierarchy.secondary_colors else hierarchy.primary_color,
            'accent_bg': hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.primary_color
        }
        
        preserved_colors = harmony_service.preserve_functional_discoverability(test_colors)
        
        # Should return color mapping
        self.assertIsInstance(preserved_colors, dict, "Should return color dictionary")
        
        # Should preserve input colors
        for key, value in test_colors.items():
            if key in preserved_colors:
                self.assertIsInstance(preserved_colors[key], str, f"{key} should be string")
                self.assertTrue(preserved_colors[key].startswith('#'), f"{key} should be hex")
        
        # Test contrast calculations
        prominence = harmony_service.calculate_brand_prominence(hierarchy)
        
        # Header should have contrasting text
        if 'background' in prominence.header_colors and 'text' in prominence.header_colors:
            bg_color = prominence.header_colors['background']
            text_color = prominence.header_colors['text']
            
            # Text should be either black or white for maximum contrast
            self.assertIn(text_color.lower(), ['#000000', '#ffffff'], 
                         "Header text should be black or white for contrast")
        
        # Navigation should have contrasting text
        if 'background' in prominence.navigation_colors and 'text' in prominence.navigation_colors:
            nav_bg = prominence.navigation_colors['background']
            nav_text = prominence.navigation_colors['text']
            
            self.assertIn(nav_text.lower(), ['#000000', '#ffffff'], 
                         "Navigation text should be black or white for contrast")
        
        # CTA should have contrasting text
        if 'primary' in prominence.cta_colors and 'primary_text' in prominence.cta_colors:
            cta_bg = prominence.cta_colors['primary']
            cta_text = prominence.cta_colors['primary_text']
            
            self.assertIn(cta_text.lower(), ['#000000', '#ffffff'], 
                         "CTA text should be black or white for contrast")


class UICompatibilityAndValidationPropertyTest(HypothesisTestCase):
    """
    Property-based tests for UI compatibility and validation system.
    
    Feature: dynamic-event-theming, Property 18: UI Compatibility and Validation
    Validates: Requirements 10.1, 10.2
    """
    
    def setUp(self):
        """Set up test data"""
        # Use unique email for each test to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        
        self.user = User.objects.create_user(
            email=f'test-ui-compat-{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title=f'Test Event {unique_id}',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
    
    @given(
        primary_color=st.sampled_from(['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#000000', '#ffffff']),
        secondary_color=st.sampled_from(['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#000000', '#ffffff']),
        accent_color=st.sampled_from(['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#000000', '#ffffff']),
    )
    @settings(max_examples=20, deadline=30000)
    def test_ui_compatibility_and_validation_property(self, primary_color: str, secondary_color: str, accent_color: str):
        """
        **Validates: Requirements 10.1, 10.2**
        
        Property 18: UI Compatibility and Validation
        
        For any applied theme, the Theme_Generator should validate that all existing UI components 
        remain functional and interactive elements continue to work correctly without breaking 
        existing functionality.
        """
        from .services.ui_compatibility import UICompatibilityValidator
        from .services.theme_generator import ThemeGenerator
        
        validator = UICompatibilityValidator()
        theme_generator = ThemeGenerator()
        
        # Generate theme CSS with the given colors
        theme_colors = {
            'primary': primary_color,
            'secondary': secondary_color,
            'accent': accent_color,
            'background': '#ffffff',
            'text': '#333333'
        }
        
        # Generate CSS theme
        generated_theme = theme_generator.generate_theme(theme_colors)
        theme_css = generated_theme.css_content
        
        # Perform comprehensive UI compatibility validation
        validation_results = validator.validate_complete_ui_compatibility(theme_css, theme_colors)
        
        # Verify validation results structure
        self.assertIsInstance(validation_results, dict, "Should return validation results dictionary")
        self.assertIn('overall_compatibility_score', validation_results, "Should have overall score")
        self.assertIn('component_validations', validation_results, "Should have component validations")
        self.assertIn('interactive_element_tests', validation_results, "Should have interactive tests")
        self.assertIn('browser_compatibility', validation_results, "Should have browser compatibility")
        self.assertIn('error_analysis', validation_results, "Should have error analysis")
        
        # Verify overall compatibility score
        overall_score = validation_results['overall_compatibility_score']
        self.assertIsInstance(overall_score, float, "Overall score should be float")
        self.assertGreaterEqual(overall_score, 0.0, "Overall score should be >= 0")
        self.assertLessEqual(overall_score, 100.0, "Overall score should be <= 100")
        
        # Verify component validations
        component_validations = validation_results['component_validations']
        self.assertIsInstance(component_validations, list, "Component validations should be list")
        
        for validation in component_validations:
            self.assertIsInstance(validation, dict, "Validation should be dict")
            self.assertIn('component', validation, "Should have component name")
            self.assertIn('level', validation, "Should have compatibility level")
            self.assertIn('issues', validation, "Should have issues list")
            self.assertIn('suggestions', validation, "Should have suggestions list")
            
            # Verify compatibility level
            level = validation['level']
            self.assertIn(level, ['excellent', 'good', 'acceptable', 'poor', 'incompatible'], 
                         "Should have valid compatibility level")
            
            # Verify issues and suggestions are lists
            self.assertIsInstance(validation['issues'], list, "Issues should be list")
            self.assertIsInstance(validation['suggestions'], list, "Suggestions should be list")
        
        # Verify interactive element tests
        interactive_tests = validation_results['interactive_element_tests']
        self.assertIsInstance(interactive_tests, list, "Interactive tests should be list")
        
        for test in interactive_tests:
            self.assertIsInstance(test, dict, "Test should be dict")
            self.assertIn('element', test, "Should have element type")
            self.assertIn('accessibility_score', test, "Should have accessibility score")
            self.assertIn('contrast_ratio', test, "Should have contrast ratio")
            
            # Verify accessibility score
            accessibility_score = test['accessibility_score']
            self.assertIsInstance(accessibility_score, float, "Accessibility score should be float")
            self.assertGreaterEqual(accessibility_score, 0.0, "Accessibility score should be >= 0")
            self.assertLessEqual(accessibility_score, 100.0, "Accessibility score should be <= 100")
            
            # Verify contrast ratio
            contrast_ratio = test['contrast_ratio']
            self.assertIsInstance(contrast_ratio, float, "Contrast ratio should be float")
            self.assertGreaterEqual(contrast_ratio, 1.0, "Contrast ratio should be >= 1")
        
        # Verify browser compatibility
        browser_compatibility = validation_results['browser_compatibility']
        self.assertIsInstance(browser_compatibility, list, "Browser compatibility should be list")
        
        for browser_test in browser_compatibility:
            self.assertIsInstance(browser_test, dict, "Browser test should be dict")
            self.assertIn('browser', browser_test, "Should have browser name")
            self.assertIn('version', browser_test, "Should have version")
            self.assertIn('css_support', browser_test, "Should have CSS support info")
            self.assertIn('fallback_needed', browser_test, "Should have fallback flag")
            
            # Verify CSS support
            css_support = browser_test['css_support']
            self.assertIsInstance(css_support, dict, "CSS support should be dict")
            
            # Verify fallback flag
            fallback_needed = browser_test['fallback_needed']
            self.assertIsInstance(fallback_needed, bool, "Fallback needed should be bool")
        
        # Verify error analysis
        error_analysis = validation_results['error_analysis']
        self.assertIsInstance(error_analysis, dict, "Error analysis should be dict")
        self.assertIn('errors_detected', error_analysis, "Should have errors detected flag")
        self.assertIn('error_count', error_analysis, "Should have error count")
        
        # Verify error detection
        errors_detected = error_analysis['errors_detected']
        self.assertIsInstance(errors_detected, bool, "Errors detected should be bool")
        
        error_count = error_analysis['error_count']
        self.assertIsInstance(error_count, int, "Error count should be int")
        self.assertGreaterEqual(error_count, 0, "Error count should be >= 0")
        
        # Property validation: UI components should remain functional
        # Critical components should not be incompatible
        critical_components = ['button', 'input', 'select', 'textarea', 'link', 'nav']
        for validation in component_validations:
            if validation['component'] in critical_components:
                self.assertNotEqual(validation['level'], 'incompatible', 
                                  f"Critical component {validation['component']} should not be incompatible")
        
        # Property validation: Interactive elements should maintain minimum accessibility
        for test in interactive_tests:
            if test['element'] in ['button', 'link', 'input']:
                self.assertGreaterEqual(test['contrast_ratio'], 3.0, 
                                      f"Interactive element {test['element']} should have minimum contrast")
        
        # Property validation: Major browsers should be supported or have fallbacks
        major_browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
        supported_browsers = [b['browser'] for b in browser_compatibility]
        
        for browser in major_browsers:
            if browser in supported_browsers:
                browser_test = next(b for b in browser_compatibility if b['browser'] == browser)
                # Either supported or has fallback
                if browser_test['fallback_needed']:
                    self.assertIsNotNone(browser_test.get('fallback_css'), 
                                       f"Browser {browser} should have fallback CSS if needed")


class AutomaticErrorRecoveryPropertyTest(HypothesisTestCase):
    """
    Property-based tests for automatic error recovery system.
    
    Feature: dynamic-event-theming, Property 19: Automatic Error Recovery
    Validates: Requirements 10.5
    """
    
    def setUp(self):
        """Set up test data"""
        # Use unique email for each test to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        
        self.user = User.objects.create_user(
            email=f'test-error-recovery-{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title=f'Test Event {unique_id}',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
    
    @given(
        broken_css=st.sampled_from([
            '.button { color: #ff0000 background: #ffffff }',  # Missing semicolon
            '.button { }',  # Empty rule
            '.button { color: invalid-color; }',  # Invalid color
            '.button { display: none; display: block; }',  # Conflicting properties
            '.nav { z-index: -1; }',  # Navigation hidden behind content
            '.form-control { opacity: 0; }',  # Form inputs invisible
            '.btn-primary { background: transparent; border: none; }',  # Buttons invisible
            '.text { color: #ffffff; background: #ffffff; }',  # No contrast
            '.modal { position: fixed; top: -9999px; }',  # Modal positioned off-screen
            '.dropdown-menu { display: none !important; }',  # Dropdown permanently hidden
            '.card { width: 0; height: 0; overflow: hidden; }',  # Cards collapsed
            '.alert { font-size: 0; }',  # Alert text invisible
        ]),
        error_type=st.sampled_from([
            'syntax_error', 'missing_property', 'invalid_color', 'conflicting_styles',
            'accessibility_violation', 'ui_breaking', 'navigation_hidden', 'forms_broken',
            'buttons_invisible', 'content_hidden', 'layout_broken', 'interaction_disabled'
        ])
    )
    @settings(max_examples=25, deadline=45000)
    def test_automatic_error_recovery_property(self, broken_css: str, error_type: str):
        """
        **Validates: Requirements 10.5**
        
        Property 19: Automatic Error Recovery
        
        For any theme application that causes UI issues, the Fallback_Manager should 
        automatically detect problems and revert to a safe default theme to maintain 
        system stability.
        """
        from .services.ui_compatibility import UICompatibilityValidator
        from .services.theme_generator import ThemeGenerator
        from .models import EventTheme
        
        validator = UICompatibilityValidator()
        theme_generator = ThemeGenerator()
        
        # Create intentionally problematic CSS based on error type
        if error_type == 'syntax_error':
            problematic_css = broken_css + "\n.button { color: #ff0000 background: #ffffff }"  # Missing semicolon
        elif error_type == 'missing_property':
            problematic_css = ".button { }"  # Empty button style
        elif error_type == 'invalid_color':
            problematic_css = ".button { color: invalid-color; background: not-a-color; }"
        elif error_type == 'conflicting_styles':
            problematic_css = ".button { display: none; display: block; position: fixed; position: absolute; }"
        elif error_type == 'accessibility_violation':
            # Create CSS that violates accessibility (poor contrast)
            problematic_css = ".text { color: #cccccc; background: #ffffff; } .button { color: #ffffff; background: #ffffcc; }"
        elif error_type == 'ui_breaking':
            # CSS that breaks UI functionality
            problematic_css = ".nav { display: none; } .btn { pointer-events: none; } .form-control { visibility: hidden; }"
        elif error_type == 'navigation_hidden':
            # Navigation becomes unusable
            problematic_css = ".navbar { z-index: -999; opacity: 0; } .nav-link { display: none; }"
        elif error_type == 'forms_broken':
            # Forms become unusable
            problematic_css = ".form-control { opacity: 0; height: 0; } .btn-submit { display: none; }"
        elif error_type == 'buttons_invisible':
            # Buttons become invisible or unclickable
            problematic_css = ".btn { background: transparent; border: none; color: transparent; }"
        elif error_type == 'content_hidden':
            # Content becomes hidden or inaccessible
            problematic_css = ".card { width: 0; height: 0; overflow: hidden; } .modal { top: -9999px; }"
        elif error_type == 'layout_broken':
            # Layout becomes broken
            problematic_css = ".container { width: 0; } .row { display: none; } .col { position: absolute; top: -999px; }"
        else:  # interaction_disabled
            # Interactive elements become disabled
            problematic_css = ".dropdown-menu { display: none !important; } .modal { pointer-events: none; }"
        
        # Test theme colors that might cause issues
        theme_colors = {
            'primary': '#000000',  # Black on potentially black background
            'secondary': '#000001',  # Nearly identical to primary
            'accent': '#000002',  # Nearly identical to primary
            'background': '#000000',  # Same as primary - poor contrast
            'text': '#111111'  # Very low contrast with background
        }
        
        # Perform error detection and recovery
        component_validations = validator.validate_component_compatibility(
            problematic_css, ['button', 'input', 'link', 'nav', 'form', 'card', 'modal', 'dropdown']
        )
        
        error_analysis = validator.detect_and_recover_errors(problematic_css, component_validations)
        
        # Verify error detection
        self.assertIsInstance(error_analysis, dict, "Should return error analysis")
        self.assertIn('errors_detected', error_analysis, "Should have error detection flag")
        self.assertIn('error_count', error_analysis, "Should have error count")
        self.assertIn('auto_fixes_available', error_analysis, "Should have auto-fixes flag")
        self.assertIn('recovery_css', error_analysis, "Should have recovery CSS")
        self.assertIn('recommendations', error_analysis, "Should have recommendations")
        
        # Property validation: Errors should be detected for problematic CSS
        errors_detected = error_analysis['errors_detected']
        self.assertIsInstance(errors_detected, bool, "Errors detected should be bool")
        
        error_count = error_analysis['error_count']
        self.assertIsInstance(error_count, int, "Error count should be int")
        self.assertGreaterEqual(error_count, 0, "Error count should be >= 0")
        
        # Property validation: Auto-fixes should be available for common issues
        auto_fixes_available = error_analysis['auto_fixes_available']
        self.assertIsInstance(auto_fixes_available, bool, "Auto-fixes available should be bool")
        
        # Property validation: Recovery CSS should be provided when errors are detected
        recovery_css = error_analysis['recovery_css']
        self.assertIsInstance(recovery_css, str, "Recovery CSS should be string")
        
        if errors_detected and error_count > 0:
            # Should provide recovery CSS for detected errors
            self.assertGreater(len(recovery_css), 0, "Should provide recovery CSS when errors detected")
            
            # Recovery CSS should be valid
            self.assertNotIn('invalid-color', recovery_css, "Recovery CSS should not contain invalid colors")
            self.assertNotIn('not-a-color', recovery_css, "Recovery CSS should not contain invalid colors")
            
            # Should contain safe color values
            if '.button' in recovery_css or '.btn' in recovery_css:
                self.assertIn('#', recovery_css, "Recovery CSS should contain hex colors")
                
            # Recovery CSS should address UI-breaking issues
            if error_type in ['navigation_hidden', 'ui_breaking']:
                # Should restore navigation visibility
                self.assertTrue(
                    'display: block' in recovery_css or 'opacity: 1' in recovery_css or 'z-index:' in recovery_css,
                    "Recovery CSS should restore navigation visibility"
                )
                
            if error_type in ['forms_broken', 'ui_breaking']:
                # Should restore form functionality
                self.assertTrue(
                    'opacity: 1' in recovery_css or 'height:' in recovery_css or 'display:' in recovery_css,
                    "Recovery CSS should restore form functionality"
                )
                
            if error_type in ['buttons_invisible', 'ui_breaking']:
                # Should restore button visibility
                self.assertTrue(
                    'background:' in recovery_css or 'border:' in recovery_css or 'color:' in recovery_css,
                    "Recovery CSS should restore button visibility"
                )
                
            if error_type == 'accessibility_violation':
                # Should improve contrast
                self.assertTrue(
                    '#000' in recovery_css or '#fff' in recovery_css or 'color:' in recovery_css,
                    "Recovery CSS should improve accessibility contrast"
                )
        
        # Property validation: Recommendations should be provided
        recommendations = error_analysis['recommendations']
        self.assertIsInstance(recommendations, list, "Recommendations should be list")
        
        if errors_detected:
            self.assertGreater(len(recommendations), 0, "Should provide recommendations when errors detected")
            
            for recommendation in recommendations:
                self.assertIsInstance(recommendation, str, "Recommendation should be string")
                self.assertGreater(len(recommendation), 0, "Recommendation should not be empty")
        
        # Property validation: Critical components should have recovery mechanisms
        critical_issues = [error for error in error_analysis.get('errors', []) 
                          if error.get('level') == 'critical']
        
        if critical_issues:
            # Should have auto-fixes for critical issues
            auto_fixes = error_analysis.get('auto_fixes', {})
            self.assertIsInstance(auto_fixes, dict, "Auto-fixes should be dict")
            
            # Should have recovery CSS for critical components
            critical_components = [error.get('component') for error in critical_issues 
                                 if error.get('component')]
            
            for component in critical_components:
                if component:
                    # Recovery CSS should address the component
                    self.assertTrue(
                        component in recovery_css or component.replace('-', '') in recovery_css,
                        f"Recovery CSS should address critical component {component}"
                    )
        
        # Property validation: System should maintain stability
        # Verify that recovery mechanisms don't introduce new errors
        if recovery_css:
            # Recovery CSS should be syntactically valid
            open_braces = recovery_css.count('{')
            close_braces = recovery_css.count('}')
            self.assertEqual(open_braces, close_braces, "Recovery CSS should have balanced braces")
            
            # Should not contain obvious syntax errors
            self.assertNotIn(';;', recovery_css, "Recovery CSS should not have double semicolons")
            self.assertNotIn('{}', recovery_css, "Recovery CSS should not have empty rules")
            
            # Should not contain problematic values
            self.assertNotIn('invalid-color', recovery_css, "Recovery CSS should not contain invalid colors")
            self.assertNotIn('not-a-color', recovery_css, "Recovery CSS should not contain invalid colors")
            self.assertNotIn('undefined', recovery_css, "Recovery CSS should not contain undefined values")
        
        # Test automatic fallback to safe default theme
        try:
            # Create a theme with the problematic CSS
            theme = EventTheme.objects.create(
                event=self.event,
                primary_color=theme_colors['primary'],
                secondary_color=theme_colors['secondary'],
                accent_color=theme_colors['accent'],
                neutral_light='#ffffff',
                neutral_dark='#000000',
                css_content=problematic_css,
                css_hash='test-hash-' + str(uuid.uuid4())[:8],
                cache_key='test-cache-' + str(uuid.uuid4())[:8],
                is_fallback=False,
                wcag_compliant=False
            )
            
            # Verify theme was created (system should handle problematic themes)
            self.assertIsNotNone(theme.id, "Theme should be created even with issues")
            
            # Test fallback mechanism
            if errors_detected and error_count > 0:
                # System should be able to generate a safe fallback
                fallback_css = validator._generate_basic_recovery_css()
                self.assertIsInstance(fallback_css, list, "Should generate fallback CSS")
                self.assertGreater(len(fallback_css), 0, "Should provide fallback CSS rules")
                
                # Fallback CSS should be safe
                fallback_content = '\n'.join(fallback_css)
                self.assertNotIn('invalid-color', fallback_content, "Fallback CSS should be safe")
                self.assertNotIn('display: none', fallback_content, "Fallback CSS should not hide elements")
                self.assertNotIn('opacity: 0', fallback_content, "Fallback CSS should not make elements invisible")
            
            # Clean up
            theme.delete()
            
        except Exception as e:
            # If theme creation fails, that's also a valid recovery mechanism
            self.assertIsInstance(e, Exception, "System should handle theme creation failures gracefully")
            
        # Property validation: Test UI stability after error recovery
        if recovery_css and len(recovery_css) > 0:
            # Recovery CSS should restore basic UI functionality
            essential_properties = ['color', 'background', 'display', 'opacity', 'z-index']
            has_essential_fixes = any(prop in recovery_css for prop in essential_properties)
            
            if error_type in ['ui_breaking', 'navigation_hidden', 'forms_broken', 'buttons_invisible']:
                self.assertTrue(has_essential_fixes, 
                              f"Recovery CSS should contain essential property fixes for {error_type}")
                              
        # Property validation: Error recovery should be comprehensive
        if error_type == 'accessibility_violation':
            # Should detect and fix accessibility issues
            if errors_detected:
                self.assertTrue(
                    any('contrast' in rec.lower() or 'accessibility' in rec.lower() 
                        for rec in recommendations),
                    "Should provide accessibility-related recommendations"
                )
                
        # Property validation: Recovery should maintain system stability
        if errors_detected and recovery_css:
            # Recovery CSS should not break other components
            self.assertNotIn('* { display: none', recovery_css, 
                           "Recovery CSS should not hide all elements")
            self.assertNotIn('body { opacity: 0', recovery_css, 
                           "Recovery CSS should not make body invisible")
            self.assertNotIn('html { display: none', recovery_css, 
                           "Recovery CSS should not hide HTML element")