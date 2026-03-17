"""
Tests for theming system security measures.

Tests comprehensive security features including:
- Secure image processing and validation
- CSS injection prevention
- Content Security Policy generation
- Malicious content detection
- Access control and audit logging
"""

import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from events.models import Event
from ..models import EventTheme, ThemeGenerationLog
from ..security import (
    ThemeSecurityValidator,
    SecureImageProcessor,
    APISecurityManager,
    PermissionManager,
    AuditLogger
)

User = get_user_model()


class ThemeSecurityValidatorTest(TestCase):
    """Test CSS security validation and sanitization."""
    
    def setUp(self):
        self.validator = ThemeSecurityValidator()
    
    def test_dangerous_css_pattern_detection(self):
        """Test detection of dangerous CSS patterns."""
        dangerous_css = """
        .malicious {
            background: url('javascript:alert("XSS")');
            color: expression(alert('XSS'));
        }
        """
        
        result = self.validator.validate_css_content(dangerous_css)
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(len(result['errors']) > 0)
        self.assertTrue(len(result['security_analysis']['dangerous_patterns_found']) > 0)
    
    def test_css_property_whitelist_validation(self):
        """Test CSS property whitelist validation."""
        safe_css = """
        .safe {
            color: #007bff;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        """
        
        result = self.validator.validate_css_content(safe_css)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_css_function_validation(self):
        """Test CSS function validation."""
        css_with_functions = """
        .test {
            color: rgb(255, 0, 0);
            transform: scale(1.2);
            background: linear-gradient(to right, #fff, #000);
        }
        """
        
        result = self.validator.validate_css_content(css_with_functions)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['security_analysis']['suspicious_functions']), 0)
    
    def test_css_size_limit(self):
        """Test CSS size limit enforcement."""
        large_css = "/* " + "x" * (self.validator.MAX_CSS_SIZE + 1) + " */"
        
        result = self.validator.validate_css_content(large_css)
        
        self.assertFalse(result['is_valid'])
        self.assertIn('too large', result['errors'][0])
    
    def test_csp_header_generation(self):
        """Test Content Security Policy header generation."""
        css_content = """
        .test {
            color: #007bff;
            background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==');
        }
        """
        
        headers = self.validator.generate_csp_headers(css_content)
        
        self.assertIn('Content-Security-Policy', headers)
        self.assertIn('style-src', headers['Content-Security-Policy'])
        self.assertIn('X-Content-Type-Options', headers)
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
    
    def test_color_value_validation(self):
        """Test color value validation."""
        valid_colors = ['#007bff', '#fff', 'rgb(255, 0, 0)', 'hsl(240, 100%, 50%)', 'red']
        invalid_colors = ['javascript:alert(1)', '#gggggg', 'rgb(300, 0, 0)', 'invalid']
        
        for color in valid_colors:
            self.assertTrue(self.validator.validate_color_value(color), f"Valid color {color} failed validation")
        
        for color in invalid_colors:
            self.assertFalse(self.validator.validate_color_value(color), f"Invalid color {color} passed validation")


class SecureImageProcessorTest(TestCase):
    """Test secure image processing and validation."""
    
    def setUp(self):
        self.processor = SecureImageProcessor()
    
    def create_test_image(self, format='PNG', size=(100, 100), mode='RGB'):
        """Create a test image for validation."""
        image = Image.new(mode, size, color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix=f'.{format.lower()}', delete=False)
        image.save(temp_file.name, format=format)
        return temp_file.name
    
    def tearDown(self):
        """Clean up temporary files."""
        # Clean up any temporary files created during tests
        pass
    
    def test_valid_image_validation(self):
        """Test validation of valid images."""
        image_path = self.create_test_image()
        
        try:
            result = self.processor.validate_image_file(image_path)
            
            self.assertTrue(result['is_valid'])
            self.assertEqual(len(result['errors']), 0)
            self.assertIn('image_info', result)
            self.assertEqual(result['image_info']['format'], 'PNG')
        finally:
            os.unlink(image_path)
    
    def test_oversized_image_rejection(self):
        """Test rejection of oversized images."""
        # Create an image larger than MAX_DIMENSIONS
        large_size = (self.processor.MAX_DIMENSIONS[0] + 100, self.processor.MAX_DIMENSIONS[1] + 100)
        image_path = self.create_test_image(size=large_size)
        
        try:
            result = self.processor.validate_image_file(image_path)
            
            self.assertFalse(result['is_valid'])
            self.assertTrue(any('too large' in error for error in result['errors']))
        finally:
            os.unlink(image_path)
    
    def test_unsupported_format_rejection(self):
        """Test rejection of unsupported image formats."""
        # Create a BMP image (not in ALLOWED_FORMATS)
        image_path = self.create_test_image(format='BMP')
        
        try:
            result = self.processor.validate_image_file(image_path)
            
            self.assertFalse(result['is_valid'])
            self.assertTrue(any('Unsupported format' in error for error in result['errors']))
        finally:
            os.unlink(image_path)
    
    def test_malicious_content_scanning(self):
        """Test malicious content scanning."""
        # Create a file with suspicious content
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.write(b'<script>alert("XSS")</script>')
        temp_file.close()
        
        try:
            scan_result = self.processor._scan_for_malicious_content(temp_file.name)
            
            self.assertTrue(scan_result['malicious_content_detected'])
            self.assertTrue(len(scan_result['suspicious_patterns']) > 0)
        finally:
            os.unlink(temp_file.name)
    
    def test_path_traversal_detection(self):
        """Test path traversal attempt detection."""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32\\config\\sam',
            '/etc/passwd',
            'C:\\Windows\\System32\\config\\SAM'
        ]
        
        for path in malicious_paths:
            self.assertTrue(self.processor._check_path_traversal(path), f"Path traversal not detected for: {path}")
    
    def test_image_sanitization(self):
        """Test image sanitization process."""
        # Create an image with transparency
        image_path = self.create_test_image(mode='RGBA')
        output_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
        
        try:
            result = self.processor.sanitize_image(image_path, output_path)
            
            self.assertTrue(result['success'])
            self.assertTrue(os.path.exists(output_path))
            
            # Verify sanitized image
            with Image.open(output_path) as sanitized_img:
                self.assertEqual(sanitized_img.mode, 'RGB')  # Transparency removed
                self.assertEqual(sanitized_img.format, 'JPEG')  # Converted to JPEG
        finally:
            os.unlink(image_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_sandboxed_processing(self):
        """Test sandboxed image processing."""
        image_path = self.create_test_image()
        output_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
        
        try:
            result = self.processor.process_image_in_sandbox(image_path, output_path)
            
            self.assertTrue(result['success'])
            self.assertTrue(len(result['sandbox_measures']) > 0)
            self.assertGreater(result['processing_time_ms'], 0)
        finally:
            os.unlink(image_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class APISecurityManagerTest(TestCase):
    """Test API security management."""
    
    def setUp(self):
        self.security_manager = APISecurityManager()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_api_request_validation(self):
        """Test comprehensive API request validation."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/api/v1/themes/', {'test': 'data'})
        request.user = self.user
        
        result = self.security_manager.validate_api_request(request, 'theme_generation')
        
        self.assertIn('is_valid', result)
        self.assertIn('security_level', result)
        self.assertIn('authentication_status', result)
        self.assertIn('rate_limit_status', result)
    
    def test_authentication_validation(self):
        """Test authentication status validation."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/api/v1/themes/')
        request.user = self.user
        
        auth_status = self.security_manager._validate_authentication(request)
        
        self.assertTrue(auth_status['is_authenticated'])
        self.assertEqual(auth_status['user_id'], self.user.id)
        self.assertFalse(auth_status['is_superuser'])


class PermissionManagerTest(TestCase):
    """Test permission management system."""
    
    def setUp(self):
        self.permission_manager = PermissionManager()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        self.event = Event.objects.create(
            title='Test Event',
            organizer=self.user
        )
    
    def test_event_owner_permissions(self):
        """Test event owner permissions."""
        result = self.permission_manager.check_permission(
            self.user, 'modify_theme', event=self.event
        )
        
        self.assertTrue(result['allowed'])
        self.assertIn('owner', result['user_roles'])
    
    def test_staff_permissions(self):
        """Test staff user permissions."""
        result = self.permission_manager.check_permission(
            self.staff_user, 'system_admin', event=self.event
        )
        
        self.assertTrue(result['allowed'])
        self.assertIn('staff', result['user_roles'])
    
    def test_permission_denial(self):
        """Test permission denial for unauthorized users."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        result = self.permission_manager.check_permission(
            other_user, 'modify_theme', event=self.event
        )
        
        self.assertFalse(result['allowed'])
        self.assertIn('Permission denied', result['reason'])


class AuditLoggerTest(TestCase):
    """Test security audit logging."""
    
    def setUp(self):
        self.audit_logger = AuditLogger()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            organizer=self.user
        )
    
    def test_security_event_logging(self):
        """Test security event logging."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/api/v1/themes/')
        request.user = self.user
        
        # Log a security event
        self.audit_logger.log_security_event(
            'test_security_event',
            self.user,
            request,
            event_id=self.event.id,
            test_data='test_value'
        )
        
        # Verify log entry was created
        log_entries = ThemeGenerationLog.objects.filter(
            event=self.event,
            operation_type='security_audit'
        )
        
        self.assertTrue(log_entries.exists())
    
    @patch('theming.security.logger')
    def test_audit_logging_error_handling(self, mock_logger):
        """Test audit logging error handling."""
        # This should not raise an exception even if logging fails
        self.audit_logger.log_security_event(
            'test_event',
            None,  # Invalid user
            None   # Invalid request
        )
        
        # Verify error was logged
        mock_logger.error.assert_called()


class IntegrationSecurityTest(TestCase):
    """Integration tests for security measures."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            organizer=self.user
        )
    
    def test_end_to_end_secure_theme_creation(self):
        """Test end-to-end secure theme creation."""
        from ..api_views_security import SecureThemeGenerationAPIView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/api/v1/themes/', {
            'colors': {
                'primary_color': '#007bff',
                'secondary_color': '#6c757d',
                'accent_color': '#28a745',
                'neutral_light': '#f8f9fa',
                'neutral_dark': '#343a40'
            }
        }, content_type='application/json')
        request.user = self.user
        
        view = SecureThemeGenerationAPIView()
        response = view.post(request, self.event.id)
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['success'])
        self.assertIn('security', response.data)
    
    def test_malicious_css_rejection(self):
        """Test rejection of malicious CSS content."""
        from ..api_views_security import SecureThemeValidationAPIView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/api/v1/themes/validate/', {
            'css_content': 'body { background: url("javascript:alert(1)"); }'
        }, content_type='application/json')
        request.user = self.user
        
        view = SecureThemeValidationAPIView()
        response = view.post(request, self.event.id)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['overall_valid'])
        self.assertFalse(response.data['css']['is_valid'])