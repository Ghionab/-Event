"""
Management command to test ColorExtractor functionality.
"""

import os
import tempfile
from django.core.management.base import BaseCommand, CommandError
from PIL import Image
from theming.services.color_extractor import ColorExtractor, extract_colors_from_file


class Command(BaseCommand):
    help = 'Test ColorExtractor functionality with sample images'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--image-path',
            type=str,
            help='Path to image file to test',
        )
        parser.add_argument(
            '--algorithm',
            type=str,
            default='kmeans',
            choices=['kmeans', 'colorthief', 'hybrid'],
            help='Color extraction algorithm to use',
        )
        parser.add_argument(
            '--num-colors',
            type=int,
            default=5,
            help='Number of colors to extract',
        )
        parser.add_argument(
            '--create-test-images',
            action='store_true',
            help='Create test images for testing',
        )
    
    def handle(self, *args, **options):
        if options['create_test_images']:
            self.create_test_images()
            return
        
        if options['image_path']:
            self.test_single_image(
                options['image_path'],
                options['algorithm'],
                options['num_colors']
            )
        else:
            self.test_with_generated_images(
                options['algorithm'],
                options['num_colors']
            )
    
    def create_test_images(self):
        """Create test images for testing."""
        self.stdout.write('Creating test images...')
        
        test_images_dir = 'test_images'
        os.makedirs(test_images_dir, exist_ok=True)
        
        # Create RGB image with distinct colors
        rgb_img = Image.new('RGB', (200, 200), color='white')
        pixels = rgb_img.load()
        
        # Add colored regions
        for i in range(0, 100):
            for j in range(0, 100):
                pixels[i, j] = (255, 0, 0)  # Red quadrant
        
        for i in range(100, 200):
            for j in range(0, 100):
                pixels[i, j] = (0, 255, 0)  # Green quadrant
        
        for i in range(0, 100):
            for j in range(100, 200):
                pixels[i, j] = (0, 0, 255)  # Blue quadrant
        
        for i in range(100, 200):
            for j in range(100, 200):
                pixels[i, j] = (255, 255, 0)  # Yellow quadrant
        
        rgb_path = os.path.join(test_images_dir, 'test_rgb.png')
        rgb_img.save(rgb_path)
        self.stdout.write(f'Created: {rgb_path}')
        
        # Create RGBA image with transparency
        rgba_img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        rgba_path = os.path.join(test_images_dir, 'test_rgba.png')
        rgba_img.save(rgba_path)
        self.stdout.write(f'Created: {rgba_path}')
        
        # Create grayscale image
        gray_img = Image.new('L', (100, 100), color=128)
        gray_path = os.path.join(test_images_dir, 'test_grayscale.png')
        gray_img.save(gray_path)
        self.stdout.write(f'Created: {gray_path}')
        
        self.stdout.write(self.style.SUCCESS('Test images created successfully!'))
    
    def test_single_image(self, image_path, algorithm, num_colors):
        """Test color extraction on a single image."""
        if not os.path.exists(image_path):
            raise CommandError(f'Image file not found: {image_path}')
        
        self.stdout.write(f'Testing color extraction on: {image_path}')
        self.stdout.write(f'Algorithm: {algorithm}')
        self.stdout.write(f'Number of colors: {num_colors}')
        self.stdout.write('-' * 50)
        
        try:
            result = extract_colors_from_file(image_path, num_colors, algorithm)
            
            self.stdout.write(f'Processing time: {result.processing_time_ms}ms')
            self.stdout.write(f'Confidence score: {result.confidence_score:.3f}')
            self.stdout.write(f'Diversity score: {result.diversity_score:.3f}')
            self.stdout.write(f'Algorithm used: {result.algorithm_used}')
            
            self.stdout.write('\nImage Properties:')
            props = result.image_properties
            self.stdout.write(f'  Size: {props.width}x{props.height}')
            self.stdout.write(f'  Format: {props.format}')
            self.stdout.write(f'  Mode: {props.mode}')
            self.stdout.write(f'  Has transparency: {props.has_transparency}')
            self.stdout.write(f'  Contrast level: {props.contrast_level:.3f}')
            self.stdout.write(f'  Noise level: {props.noise_level:.3f}')
            
            self.stdout.write('\nExtracted Colors:')
            for i, color in enumerate(result.colors, 1):
                self.stdout.write(
                    f'  {i}. {color.color} ({color.name}) - '
                    f'Confidence: {color.confidence:.3f}, '
                    f'Frequency: {color.frequency:.3f}'
                )
            
            self.stdout.write('\nMetadata:')
            for key, value in result.metadata.items():
                self.stdout.write(f'  {key}: {value}')
            
            self.stdout.write(self.style.SUCCESS('\nColor extraction completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Color extraction failed: {str(e)}'))
            raise CommandError(str(e))
    
    def test_with_generated_images(self, algorithm, num_colors):
        """Test color extraction with generated test images."""
        self.stdout.write('Testing ColorExtractor with generated images...')
        
        # Create temporary test images
        test_cases = [
            ('RGB with distinct colors', self.create_rgb_test_image),
            ('RGBA with transparency', self.create_rgba_test_image),
            ('Grayscale image', self.create_grayscale_test_image),
            ('Monochromatic image', self.create_monochromatic_test_image),
        ]
        
        for test_name, create_func in test_cases:
            self.stdout.write(f'\n{"-" * 60}')
            self.stdout.write(f'Testing: {test_name}')
            self.stdout.write(f'{"-" * 60}')
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                try:
                    img = create_func()
                    img.save(temp_file.name)
                    
                    result = extract_colors_from_file(temp_file.name, num_colors, algorithm)
                    
                    self.stdout.write(f'Colors extracted: {len(result.colors)}')
                    self.stdout.write(f'Confidence: {result.confidence_score:.3f}')
                    self.stdout.write(f'Diversity: {result.diversity_score:.3f}')
                    self.stdout.write(f'Processing time: {result.processing_time_ms}ms')
                    
                    for i, color in enumerate(result.colors, 1):
                        self.stdout.write(
                            f'  {i}. {color.color} ({color.name}) - '
                            f'C: {color.confidence:.2f}, F: {color.frequency:.2f}'
                        )
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed: {str(e)}'))
                
                finally:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
        
        self.stdout.write(self.style.SUCCESS('\nAll tests completed!'))
    
    def create_rgb_test_image(self):
        """Create RGB test image with distinct colors."""
        img = Image.new('RGB', (100, 100), color='white')
        pixels = img.load()
        
        # Create colored regions
        for i in range(0, 50):
            for j in range(0, 50):
                pixels[i, j] = (255, 0, 0)  # Red
        
        for i in range(50, 100):
            for j in range(0, 50):
                pixels[i, j] = (0, 255, 0)  # Green
        
        for i in range(0, 50):
            for j in range(50, 100):
                pixels[i, j] = (0, 0, 255)  # Blue
        
        return img
    
    def create_rgba_test_image(self):
        """Create RGBA test image with transparency."""
        return Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    
    def create_grayscale_test_image(self):
        """Create grayscale test image."""
        return Image.new('L', (100, 100), color=128)
    
    def create_monochromatic_test_image(self):
        """Create monochromatic test image."""
        img = Image.new('RGB', (100, 100), color=(100, 150, 200))
        pixels = img.load()
        
        # Add slight variations
        for i in range(100):
            for j in range(100):
                variation = (i + j) % 20 - 10  # Small variation
                r = max(0, min(255, 100 + variation))
                g = max(0, min(255, 150 + variation))
                b = max(0, min(255, 200 + variation))
                pixels[i, j] = (r, g, b)
        
        return img