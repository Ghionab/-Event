"""
Unit tests for ColorExtractor service.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np

from django.test import TestCase
from theming.services.color_extractor import (
    ColorExtractor, 
    ExtractedColor, 
    ImageProperties,
    ColorExtractionResult,
    extract_colors_from_file,
    is_supported_format,
    get_supported_formats
)


class ColorExtractorTest(TestCase):
    """Test ColorExtractor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = ColorExtractor(num_colors=3)
        
        # Create test images
        self.test_images = {}
        self._create_test_images()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up test images
        for image_path in self.test_images.values():
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    def _create_test_images(self):
        """Create test images for testing."""
        # Create a simple RGB image with known colors
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), color='red')
            # Add some blue and green areas
            pixels = img.load()
            for i in range(30, 70):
                for j in range(30, 70):
                    pixels[i, j] = (0, 0, 255)  # Blue center
            for i in range(10, 30):
                for j in range(10, 30):
                    pixels[i, j] = (0, 255, 0)  # Green corner
            img.save(f.name, 'PNG')
            self.test_images['rgb'] = f.name
        
        # Create RGBA image with transparency
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGBA', (50, 50), color=(255, 0, 0, 128))
            img.save(f.name, 'PNG')
            self.test_images['rgba'] = f.name
        
        # Create grayscale image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('L', (50, 50), color=128)
            img.save(f.name, 'PNG')
            self.test_images['grayscale'] = f.name
    
    def test_extract_colors_basic(self):
        """Test basic color extraction."""
        result = self.extractor.extract_colors(self.test_images['rgb'])
        
        self.assertIsInstance(result, ColorExtractionResult)
        self.assertGreater(len(result.colors), 0)
        self.assertLessEqual(len(result.colors), 3)
        
        # Check that we got the expected colors (red, blue, green)
        extracted_colors = [color.rgb for color in result.colors]
        self.assertTrue(any(r > 200 and g < 50 and b < 50 for r, g, b in extracted_colors))  # Red
        
    def test_supported_formats(self):
        """Test supported format validation."""
        # Test valid format
        self.assertTrue(is_supported_format(self.test_images['rgb']))
        
        # Test format list
        formats = get_supported_formats()
        self.assertIn('PNG', formats)
        self.assertIn('JPEG', formats)
        
    def test_image_properties_analysis(self):
        """Test image properties analysis."""
        properties = self.extractor.analyze_image_properties(self.test_images['rgb'])
        
        self.assertIsInstance(properties, ImageProperties)
        self.assertEqual(properties.width, 100)
        self.assertEqual(properties.height, 100)
        self.assertEqual(properties.format, 'PNG')
        self.assertFalse(properties.has_transparency)
        
    def test_rgba_image_handling(self):
        """Test handling of RGBA images with transparency."""
        result = self.extractor.extract_colors(self.test_images['rgba'])
        
        self.assertIsInstance(result, ColorExtractionResult)
        self.assertGreater(len(result.colors), 0)
        
        # Should handle transparency properly
        properties = result.image_properties
        self.assertTrue(properties.has_transparency)
    
    def test_confidence_scoring(self):
        """Test confidence scoring system."""
        result = self.extractor.extract_colors(self.test_images['rgb'])
        
        for color in result.colors:
            self.assertIsInstance(color.confidence, float)
            self.assertGreaterEqual(color.confidence, 0.0)
            self.assertLessEqual(color.confidence, 1.0)
        
        # Colors should be sorted by confidence/frequency
        confidences = [c.confidence for c in result.colors]
        self.assertEqual(confidences, sorted(confidences, reverse=True))
    
    def test_color_diversity_calculation(self):
        """Test color diversity scoring."""
        result = self.extractor.extract_colors(self.test_images['rgb'])
        
        self.assertIsInstance(result.diversity_score, float)
        self.assertGreaterEqual(result.diversity_score, 0.0)
        self.assertLessEqual(result.diversity_score, 1.0)
    
    def test_different_algorithms(self):
        """Test different extraction algorithms."""
        # Test K-means
        result_kmeans = self.extractor.extract_colors(self.test_images['rgb'], algorithm='kmeans')
        self.assertEqual(result_kmeans.algorithm_used, 'kmeans')
        
        # Test ColorThief
        result_colorthief = self.extractor.extract_colors(self.test_images['rgb'], algorithm='colorthief')
        self.assertEqual(result_colorthief.algorithm_used, 'colorthief')
        
        # Test hybrid
        result_hybrid = self.extractor.extract_colors(self.test_images['rgb'], algorithm='hybrid')
        self.assertEqual(result_hybrid.algorithm_used, 'hybrid')
    
    def test_invalid_image_path(self):
        """Test handling of invalid image paths."""
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_colors('nonexistent_image.png')
    
    def test_unsupported_format(self):
        """Test handling of unsupported image formats."""
        # Create a text file with image extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'This is not an image')
            f.flush()
            
            with self.assertRaises(Exception):
                self.extractor.extract_colors(f.name)
            
            os.unlink(f.name)
    
    def test_color_name_generation(self):
        """Test color name generation."""
        result = self.extractor.extract_colors(self.test_images['rgb'])
        
        for color in result.colors:
            self.assertIsInstance(color.name, str)
            self.assertGreater(len(color.name), 0)
    
    def test_hex_color_format(self):
        """Test hex color format."""
        result = self.extractor.extract_colors(self.test_images['rgb'])
        
        for color in result.colors:
            self.assertRegex(color.color, r'^#[0-9a-f]{6}$')
    
    def test_processing_time_tracking(self):
        """Test processing time tracking."""
        result = self.extractor.extract_colors(self.test_images['rgb'])
        
        self.assertIsInstance(result.processing_time_ms, int)
        self.assertGreater(result.processing_time_ms, 0)
    
    def test_metadata_inclusion(self):
        """Test metadata inclusion in results."""
        result = self.extractor.extract_colors(self.test_images['rgb'])
        
        self.assertIsInstance(result.metadata, dict)
        self.assertIn('num_colors_requested', result.metadata)
        self.assertIn('num_colors_extracted', result.metadata)
        self.assertIn('preprocessing_applied', result.metadata)
    
    @patch('theming.services.color_extractor.KMeans')
    def test_kmeans_failure_fallback(self, mock_kmeans):
        """Test fallback when K-means fails."""
        # Make K-means raise an exception
        mock_kmeans.side_effect = Exception("K-means failed")
        
        # Should fallback to simple extraction
        result = self.extractor.extract_colors(self.test_images['rgb'], algorithm='kmeans')
        self.assertIsInstance(result, ColorExtractionResult)
    
    def test_large_image_resizing(self):
        """Test automatic resizing of large images."""
        # Create a large image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            large_img = Image.new('RGB', (2000, 2000), color='blue')
            large_img.save(f.name, 'PNG')
            
            result = self.extractor.extract_colors(f.name)
            
            # Should indicate image was resized
            self.assertTrue(result.metadata.get('image_resized', False))
            
            os.unlink(f.name)
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test extract_colors_from_file
        result = extract_colors_from_file(self.test_images['rgb'], num_colors=2)
        self.assertIsInstance(result, ColorExtractionResult)
        self.assertLessEqual(len(result.colors), 2)
        
        # Test is_supported_format
        self.assertTrue(is_supported_format(self.test_images['rgb']))
        
        # Test get_supported_formats
        formats = get_supported_formats()
        self.assertIsInstance(formats, list)
        self.assertGreater(len(formats), 0)


class ExtractedColorTest(TestCase):
    """Test ExtractedColor dataclass."""
    
    def test_extracted_color_creation(self):
        """Test ExtractedColor creation."""
        color = ExtractedColor(
            color='#ff0000',
            rgb=(255, 0, 0),
            confidence=0.9,
            frequency=0.3,
            name='Red'
        )
        
        self.assertEqual(color.color, '#ff0000')
        self.assertEqual(color.rgb, (255, 0, 0))
        self.assertEqual(color.confidence, 0.9)
        self.assertEqual(color.frequency, 0.3)
        self.assertEqual(color.name, 'Red')


class ImagePropertiesTest(TestCase):
    """Test ImageProperties dataclass."""
    
    def test_image_properties_creation(self):
        """Test ImageProperties creation."""
        props = ImageProperties(
            width=100,
            height=100,
            format='PNG',
            mode='RGB',
            has_transparency=False,
            dominant_colors_count=5,
            noise_level=0.1,
            contrast_level=0.8
        )
        
        self.assertEqual(props.width, 100)
        self.assertEqual(props.height, 100)
        self.assertEqual(props.format, 'PNG')
        self.assertEqual(props.mode, 'RGB')
        self.assertFalse(props.has_transparency)
        self.assertEqual(props.dominant_colors_count, 5)
        self.assertEqual(props.noise_level, 0.1)
        self.assertEqual(props.contrast_level, 0.8)