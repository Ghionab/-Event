"""
Integration tests for ColorExtractor with Django views.
"""

import os
import tempfile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from events.models import Event
from theming.models import EventTheme, ColorPalette

User = get_user_model()


class ColorExtractorIntegrationTest(TestCase):
    """Test ColorExtractor integration with Django views."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            organizer=self.user,
            start_date='2024-12-01T10:00:00Z',
            end_date='2024-12-02T18:00:00Z',
            venue_name='Test Location'
        )
        
        # Create test image
        self.test_image = self._create_test_image()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_image):
            os.unlink(self.test_image)
    
    def _create_test_image(self):
        """Create a test image file."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), color='red')
            # Add some blue area
            pixels = img.load()
            for i in range(30, 70):
                for j in range(30, 70):
                    pixels[i, j] = (0, 0, 255)  # Blue center
            img.save(f.name, 'PNG')
            return f.name
    
    def test_extract_colors_view_integration(self):
        """Test color extraction through Django view."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Read test image
        with open(self.test_image, 'rb') as img_file:
            uploaded_file = SimpleUploadedFile(
                name='test_image.png',
                content=img_file.read(),
                content_type='image/png'
            )
        
        # Make request to extract colors
        url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
        response = self.client.post(url, {
            'image': uploaded_file,
            'algorithm': 'kmeans'
        })
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('extracted_colors', data)
        self.assertIn('overall_confidence', data)
        self.assertIn('processing_time_ms', data)
        self.assertIn('algorithm_used', data)
        
        # Verify colors were extracted
        colors = data['extracted_colors']
        self.assertGreater(len(colors), 0)
        
        # Check color format
        for color in colors:
            self.assertIn('color', color)
            self.assertIn('confidence', color)
            self.assertIn('frequency', color)
            self.assertIn('name', color)
            self.assertRegex(color['color'], r'^#[0-9a-f]{6}$')
        
        # Verify database objects were created
        theme = EventTheme.objects.get(event=self.event)
        self.assertIsNotNone(theme)
        
        palette = ColorPalette.objects.get(theme=theme)
        self.assertIsNotNone(palette)
        self.assertEqual(len(palette.extracted_colors), len(colors))
        self.assertEqual(palette.extraction_algorithm, 'kmeans')
    
    def test_unsupported_format_handling(self):
        """Test handling of unsupported image formats."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create a text file disguised as an image
        uploaded_file = SimpleUploadedFile(
            name='fake_image.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
        response = self.client.post(url, {'image': uploaded_file})
        
        # Should return error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('error', data)
    
    def test_no_image_provided(self):
        """Test handling when no image is provided."""
        self.client.login(email='test@example.com', password='testpass123')
        
        url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
        response = self.client.post(url, {})
        
        # Should return error
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('No image file provided', data['error'])
    
    def test_large_file_handling(self):
        """Test handling of large files."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create a large fake file (simulate 11MB)
        large_content = b'x' * (11 * 1024 * 1024)
        uploaded_file = SimpleUploadedFile(
            name='large_image.png',
            content=large_content,
            content_type='image/png'
        )
        
        url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
        response = self.client.post(url, {'image': uploaded_file})
        
        # Should return error for file too large
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('too large', data['error'])
    
    def test_different_algorithms(self):
        """Test different extraction algorithms."""
        self.client.login(email='test@example.com', password='testpass123')
        
        algorithms = ['kmeans', 'colorthief', 'hybrid']
        
        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                # Read test image
                with open(self.test_image, 'rb') as img_file:
                    uploaded_file = SimpleUploadedFile(
                        name=f'test_image_{algorithm}.png',
                        content=img_file.read(),
                        content_type='image/png'
                    )
                
                url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
                response = self.client.post(url, {
                    'image': uploaded_file,
                    'algorithm': algorithm
                })
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertTrue(data['success'])
                self.assertEqual(data['algorithm_used'], algorithm)


class CompleteSystemIntegrationTest(TestCase):
    """Test complete end-to-end theming system workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='organizer'
        )
        self.event = Event.objects.create(
            title='Integration Test Event',
            description='Test Description',
            organizer=self.user,
            start_date='2024-12-01T10:00:00Z',
            end_date='2024-12-02T18:00:00Z',
            venue_name='Test Location'
        )
        
        # Create test image with multiple colors
        self.test_image = self._create_complex_test_image()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_image):
            os.unlink(self.test_image)
    
    def _create_complex_test_image(self):
        """Create a complex test image with multiple colors."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (200, 200), color='white')
            pixels = img.load()
            
            # Add red section
            for i in range(0, 100):
                for j in range(0, 100):
                    pixels[i, j] = (220, 20, 60)  # Crimson
            
            # Add blue section
            for i in range(100, 200):
                for j in range(0, 100):
                    pixels[i, j] = (30, 144, 255)  # Dodger blue
            
            # Add green section
            for i in range(0, 100):
                for j in range(100, 200):
                    pixels[i, j] = (50, 205, 50)  # Lime green
            
            # Add purple section
            for i in range(100, 200):
                for j in range(100, 200):
                    pixels[i, j] = (138, 43, 226)  # Blue violet
            
            img.save(f.name, 'PNG')
            return f.name
    
    def test_complete_theme_generation_workflow(self):
        """Test complete workflow from color extraction to theme application."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Step 1: Extract colors from image
        with open(self.test_image, 'rb') as img_file:
            uploaded_file = SimpleUploadedFile(
                name='brand_image.png',
                content=img_file.read(),
                content_type='image/png'
            )
        
        extract_url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
        extract_response = self.client.post(extract_url, {
            'image': uploaded_file,
            'algorithm': 'kmeans'
        })
        
        self.assertEqual(extract_response.status_code, 200)
        extract_data = extract_response.json()
        self.assertTrue(extract_data['success'])
        
        # Step 2: Generate theme from extracted colors
        generate_url = reverse('theming:generate_theme', kwargs={'event_id': self.event.id})
        generate_response = self.client.post(generate_url, {
            'variation': 'light',
            'accessibility_level': 'AA'
        })
        
        self.assertEqual(generate_response.status_code, 200)
        generate_data = generate_response.json()
        self.assertTrue(generate_data['success'])
        self.assertIn('theme_id', generate_data)
        self.assertIn('css_content', generate_data)
        
        # Step 3: Verify theme was created in database
        theme = EventTheme.objects.get(event=self.event)
        self.assertIsNotNone(theme)
        self.assertTrue(theme.wcag_compliant)
        self.assertIsNotNone(theme.css_content)
        self.assertGreater(len(theme.css_content), 0)
        
        # Step 4: Test theme application in different portals
        portals = ['staff', 'participant', 'organizer']
        
        for portal in portals:
            with self.subTest(portal=portal):
                portal_url = reverse('theming:apply_theme', kwargs={
                    'event_id': self.event.id,
                    'portal': portal
                })
                portal_response = self.client.get(portal_url)
                
                self.assertEqual(portal_response.status_code, 200)
                self.assertIn('text/css', portal_response['Content-Type'])
                
                # Verify CSS contains portal-specific styles
                css_content = portal_response.content.decode('utf-8')
                self.assertIn(f'.{portal}-portal', css_content)
                self.assertIn('--primary-color:', css_content)
                self.assertIn('--secondary-color:', css_content)
        
        # Step 5: Test theme preview
        preview_url = reverse('theming:preview_theme', kwargs={'event_id': self.event.id})
        preview_response = self.client.get(preview_url)
        
        self.assertEqual(preview_response.status_code, 200)
        self.assertContains(preview_response, 'Theme Preview')
        self.assertContains(preview_response, theme.primary_color)
    
    def test_fallback_system_integration(self):
        """Test fallback system when color extraction fails."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create invalid image file
        invalid_file = SimpleUploadedFile(
            name='invalid.png',
            content=b'invalid image data',
            content_type='image/png'
        )
        
        # Attempt color extraction (should fail)
        extract_url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
        extract_response = self.client.post(extract_url, {'image': invalid_file})
        
        # Should still generate theme using fallback
        generate_url = reverse('theming:generate_theme', kwargs={'event_id': self.event.id})
        generate_response = self.client.post(generate_url, {
            'use_fallback': True,
            'industry': 'technology'
        })
        
        self.assertEqual(generate_response.status_code, 200)
        generate_data = generate_response.json()
        self.assertTrue(generate_data['success'])
        self.assertTrue(generate_data.get('used_fallback', False))
        
        # Verify fallback theme was created
        theme = EventTheme.objects.get(event=self.event)
        self.assertTrue(theme.is_fallback)
        self.assertIsNotNone(theme.css_content)
    
    def test_async_processing_integration(self):
        """Test asynchronous theme generation with WebSocket notifications."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Start async theme generation
        async_url = reverse('theming:generate_theme_async', kwargs={'event_id': self.event.id})
        
        with open(self.test_image, 'rb') as img_file:
            uploaded_file = SimpleUploadedFile(
                name='async_test.png',
                content=img_file.read(),
                content_type='image/png'
            )
        
        async_response = self.client.post(async_url, {
            'image': uploaded_file,
            'algorithm': 'hybrid'
        })
        
        self.assertEqual(async_response.status_code, 202)  # Accepted
        async_data = async_response.json()
        self.assertIn('task_id', async_data)
        self.assertIn('status_url', async_data)
        
        # Check task status
        task_id = async_data['task_id']
        status_url = reverse('theming:task_status', kwargs={'task_id': task_id})
        
        # Poll for completion (in real scenario, would use WebSocket)
        import time
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            status_response = self.client.get(status_url)
            self.assertEqual(status_response.status_code, 200)
            
            status_data = status_response.json()
            if status_data['status'] == 'completed':
                self.assertTrue(status_data['success'])
                self.assertIn('theme_id', status_data)
                break
            elif status_data['status'] == 'failed':
                self.fail(f"Async task failed: {status_data.get('error')}")
            
            time.sleep(0.5)
            attempts += 1
        
        if attempts >= max_attempts:
            self.fail("Async task did not complete within expected time")
    
    def test_cross_portal_consistency(self):
        """Test theme consistency across different portals."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Generate theme
        with open(self.test_image, 'rb') as img_file:
            uploaded_file = SimpleUploadedFile(
                name='consistency_test.png',
                content=img_file.read(),
                content_type='image/png'
            )
        
        extract_url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
        self.client.post(extract_url, {'image': uploaded_file})
        
        generate_url = reverse('theming:generate_theme', kwargs={'event_id': self.event.id})
        self.client.post(generate_url, {'variation': 'light'})
        
        # Get CSS for all portals
        portals = ['staff', 'participant', 'organizer']
        portal_css = {}
        
        for portal in portals:
            portal_url = reverse('theming:apply_theme', kwargs={
                'event_id': self.event.id,
                'portal': portal
            })
            response = self.client.get(portal_url)
            portal_css[portal] = response.content.decode('utf-8')
        
        # Extract color variables from each portal's CSS
        import re
        color_pattern = r'--(\w+-color):\s*(#[0-9a-f]{6})'
        
        portal_colors = {}
        for portal, css in portal_css.items():
            colors = dict(re.findall(color_pattern, css))
            portal_colors[portal] = colors
        
        # Verify core colors are consistent across portals
        core_colors = ['primary-color', 'secondary-color', 'accent-color']
        
        for color in core_colors:
            if color in portal_colors['staff']:
                staff_color = portal_colors['staff'][color]
                
                for portal in ['participant', 'organizer']:
                    if color in portal_colors[portal]:
                        self.assertEqual(
                            portal_colors[portal][color], 
                            staff_color,
                            f"{color} should be consistent across portals"
                        )
    
    def test_accessibility_compliance_integration(self):
        """Test accessibility compliance throughout the system."""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Generate theme with accessibility requirements
        with open(self.test_image, 'rb') as img_file:
            uploaded_file = SimpleUploadedFile(
                name='accessibility_test.png',
                content=img_file.read(),
                content_type='image/png'
            )
        
        extract_url = reverse('theming:extract_colors', kwargs={'event_id': self.event.id})
        self.client.post(extract_url, {'image': uploaded_file})
        
        generate_url = reverse('theming:generate_theme', kwargs={'event_id': self.event.id})
        generate_response = self.client.post(generate_url, {
            'accessibility_level': 'AAA',
            'high_contrast': True
        })
        
        self.assertEqual(generate_response.status_code, 200)
        
        # Verify theme meets accessibility requirements
        theme = EventTheme.objects.get(event=self.event)
        self.assertTrue(theme.wcag_compliant)
        
        # Test accessibility validation endpoint
        validate_url = reverse('theming:validate_accessibility', kwargs={'event_id': self.event.id})
        validate_response = self.client.get(validate_url)
        
        self.assertEqual(validate_response.status_code, 200)
        validate_data = validate_response.json()
        
        self.assertTrue(validate_data['compliant'])
        self.assertGreaterEqual(validate_data['contrast_ratio'], 7.0)  # AAA level
        self.assertGreaterEqual(validate_data['accessibility_score'], 90.0)