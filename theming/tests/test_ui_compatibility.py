"""
Unit tests for UI Compatibility and Validation Service.

These tests complement the property-based tests by testing specific scenarios
and edge cases for the UI compatibility validation system.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from events.models import Event
from theming.services.ui_compatibility import (
    UICompatibilityValidator, CompatibilityLevel, ComponentValidation,
    InteractiveElementTest, BrowserCompatibility
)
from theming.services.theme_generator import ThemeGenerator
from theming.models import EventTheme
import uuid

User = get_user_model()


class UICompatibilityValidatorTest(TestCase):
    """Test the UI compatibility validator service."""
    
    def setUp(self):
        """Set up test data."""
        unique_id = str(uuid.uuid4())[:8]
        
        self.user = User.objects.create_user(
            email=f'test-ui-{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.event = Event.objects.create(
            title=f'Test Event {unique_id}',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
        
        self.validator = UICompatibilityValidator()
        self.theme_generator = ThemeGenerator()
    
    def test_validate_component_compatibility_with_good_css(self):
        """Test component validation with well-formed CSS."""
        good_css = """
        .button {
            background-color: #007bff;
            color: #ffffff;
            border: 1px solid #007bff;
            padding: 0.375rem 0.75rem;
            border-radius: 0.25rem;
        }
        .input {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
            padding: 0.375rem 0.75rem;
        }
        """
        
        validations = self.validator.validate_component_compatibility(
            good_css, ['button', 'input']
        )
        
        self.assertEqual(len(validations), 2)
        
        for validation in validations:
            self.assertIsInstance(validation, ComponentValidation)
            self.assertIn(validation.component_name, ['button', 'input'])
            self.assertIn(validation.compatibility_level, [
                CompatibilityLevel.EXCELLENT, CompatibilityLevel.GOOD
            ])
    
    def test_validate_component_compatibility_with_poor_css(self):
        """Test component validation with problematic CSS."""
        poor_css = """
        .button {
            color: #cccccc;
            background-color: #dddddd;
        }
        .input {
            /* Missing essential properties */
        }
        """
        
        validations = self.validator.validate_component_compatibility(
            poor_css, ['button', 'input']
        )
        
        self.assertEqual(len(validations), 2)
        
        # Button should have contrast issues
        button_validation = next(v for v in validations if v.component_name == 'button')
        self.assertGreater(len(button_validation.issues), 0)
        
        # Input should have missing properties
        input_validation = next(v for v in validations if v.component_name == 'input')
        self.assertGreater(len(input_validation.issues), 0)
    
    def test_interactive_elements_testing(self):
        """Test interactive element accessibility testing."""
        theme_colors = {
            'primary': '#007bff',
            'secondary': '#6c757d',
            'accent': '#28a745',
            'background': '#ffffff',
            'text': '#333333',
            'button_bg': '#007bff',
            'button_text': '#ffffff',
            'link': '#007bff'
        }
        
        tests = self.validator.test_interactive_elements(theme_colors)
        
        self.assertGreater(len(tests), 0)
        
        for test in tests:
            self.assertIsInstance(test, InteractiveElementTest)
            self.assertIsInstance(test.accessibility_score, float)
            self.assertGreaterEqual(test.accessibility_score, 0.0)
            self.assertLessEqual(test.accessibility_score, 100.0)
            self.assertIsInstance(test.contrast_ratio, float)
            self.assertGreaterEqual(test.contrast_ratio, 1.0)
    
    def test_browser_compatibility_verification(self):
        """Test browser compatibility verification."""
        modern_css = """
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        .card {
            background: var(--primary-color);
            backdrop-filter: blur(10px);
        }
        """
        
        compatibility = self.validator.verify_browser_compatibility(modern_css)
        
        self.assertGreater(len(compatibility), 0)
        
        for browser_test in compatibility:
            self.assertIsInstance(browser_test, BrowserCompatibility)
            self.assertIsInstance(browser_test.browser, str)
            self.assertIsInstance(browser_test.version, str)
            self.assertIsInstance(browser_test.css_support, dict)
            self.assertIsInstance(browser_test.fallback_needed, bool)
            
            if browser_test.fallback_needed:
                self.assertIsNotNone(browser_test.fallback_css)
    
    def test_error_detection_and_recovery(self):
        """Test automatic error detection and recovery."""
        broken_css = """
        .button {
            color: #ff0000 /* Missing semicolon */
            background: invalid-color;
            display: none;
            display: block;
        }
        """
        
        # First validate components to get validation results
        validations = self.validator.validate_component_compatibility(
            broken_css, ['button']
        )
        
        # Then test error detection and recovery
        error_analysis = self.validator.detect_and_recover_errors(
            broken_css, validations
        )
        
        self.assertIsInstance(error_analysis, dict)
        self.assertIn('errors_detected', error_analysis)
        self.assertIn('error_count', error_analysis)
        self.assertIn('recovery_css', error_analysis)
        self.assertIn('recommendations', error_analysis)
        
        # Should detect errors in broken CSS
        self.assertTrue(error_analysis['errors_detected'])
        self.assertGreater(error_analysis['error_count'], 0)
        
        # Should provide recovery CSS
        recovery_css = error_analysis['recovery_css']
        self.assertIsInstance(recovery_css, str)
        self.assertGreater(len(recovery_css), 0)
        
        # Recovery CSS should be valid
        self.assertNotIn('invalid-color', recovery_css)
        self.assertIn('#', recovery_css)  # Should contain hex colors
    
    def test_complete_ui_compatibility_validation(self):
        """Test the comprehensive UI compatibility validation."""
        theme_colors = {
            'primary': '#007bff',
            'secondary': '#6c757d',
            'accent': '#28a745',
            'background': '#ffffff',
            'text': '#333333'
        }
        
        # Generate a theme
        generated_theme = self.theme_generator.generate_theme(theme_colors)
        
        # Perform complete validation
        results = self.validator.validate_complete_ui_compatibility(
            generated_theme.css_content, theme_colors
        )
        
        # Verify results structure
        self.assertIsInstance(results, dict)
        self.assertIn('overall_compatibility_score', results)
        self.assertIn('component_validations', results)
        self.assertIn('interactive_element_tests', results)
        self.assertIn('browser_compatibility', results)
        self.assertIn('error_analysis', results)
        self.assertIn('recommendations', results)
        
        # Verify overall score
        score = results['overall_compatibility_score']
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
        
        # Verify component validations
        validations = results['component_validations']
        self.assertIsInstance(validations, list)
        
        # Verify interactive tests
        tests = results['interactive_element_tests']
        self.assertIsInstance(tests, list)
        
        # Verify browser compatibility
        browser_tests = results['browser_compatibility']
        self.assertIsInstance(browser_tests, list)
        
        # Verify error analysis
        error_analysis = results['error_analysis']
        self.assertIsInstance(error_analysis, dict)
        
        # Verify recommendations
        recommendations = results['recommendations']
        self.assertIsInstance(recommendations, list)
    
    def test_contrast_ratio_calculation(self):
        """Test WCAG contrast ratio calculation."""
        # Test high contrast (black on white)
        high_contrast = self.validator._calculate_contrast_ratio('#000000', '#ffffff')
        self.assertGreaterEqual(high_contrast, 20.0)  # Should be 21:1
        
        # Test low contrast (light gray on white)
        low_contrast = self.validator._calculate_contrast_ratio('#cccccc', '#ffffff')
        self.assertLess(low_contrast, 4.5)
        
        # Test medium contrast (dark blue on white)
        medium_contrast = self.validator._calculate_contrast_ratio('#003366', '#ffffff')
        self.assertGreaterEqual(medium_contrast, 4.5)
    
    def test_css_syntax_validation(self):
        """Test CSS syntax validation."""
        # Valid CSS
        valid_css = """
        .button {
            color: #ffffff;
            background-color: #007bff;
        }
        """
        
        valid_errors = self.validator._validate_css_syntax(valid_css)
        self.assertEqual(len(valid_errors), 0)
        
        # Invalid CSS with unmatched braces
        invalid_css = """
        .button {
            color: #ffffff;
            background-color: #007bff;
        /* Missing closing brace */
        """
        
        invalid_errors = self.validator._validate_css_syntax(invalid_css)
        self.assertGreater(len(invalid_errors), 0)
        
        # Check error structure
        for error in invalid_errors:
            self.assertIsInstance(error, dict)
            self.assertIn('type', error)
            self.assertIn('level', error)
            self.assertIn('message', error)
    
    def test_color_adjustment_for_accessibility(self):
        """Test automatic color adjustment for accessibility compliance."""
        # Test with poor contrast colors
        poor_text = '#cccccc'
        background = '#ffffff'
        
        adjusted = self.validator._adjust_color_for_contrast(poor_text, background)
        
        # Adjusted color should have better contrast
        new_contrast = self.validator._calculate_contrast_ratio(adjusted, background)
        old_contrast = self.validator._calculate_contrast_ratio(poor_text, background)
        
        self.assertGreaterEqual(new_contrast, old_contrast)
        
        # Should be a valid hex color
        self.assertTrue(adjusted.startswith('#'))
        self.assertEqual(len(adjusted), 7)
    
    def test_compatibility_report_generation(self):
        """Test generation of human-readable compatibility report."""
        theme_colors = {
            'primary': '#007bff',
            'secondary': '#6c757d',
            'accent': '#28a745',
            'background': '#ffffff',
            'text': '#333333'
        }
        
        # Generate theme and validate
        generated_theme = self.theme_generator.generate_theme(theme_colors)
        validation_results = self.validator.validate_complete_ui_compatibility(
            generated_theme.css_content, theme_colors
        )
        
        # Generate report
        report = self.validator.generate_compatibility_report(validation_results)
        
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        
        # Report should contain key sections
        self.assertIn('UI Compatibility Validation Report', report)
        self.assertIn('Overall Compatibility Score', report)
        self.assertIn('Component Validation Summary', report)
        self.assertIn('Browser Compatibility', report)
        
        # Should contain score
        score = validation_results['overall_compatibility_score']
        self.assertIn(f'{score:.1f}/100', report)
    
    def test_theme_with_real_components(self):
        """Test theme validation with HTML component samples."""
        theme_colors = {
            'primary': '#007bff',
            'secondary': '#6c757d',
            'accent': '#28a745',
            'background': '#ffffff',
            'text': '#333333'
        }
        
        generated_theme = self.theme_generator.generate_theme(theme_colors)
        
        # Sample HTML components
        component_samples = {
            'button': '<button class="btn btn-primary">Click me</button>',
            'input': '<input type="text" class="form-control" placeholder="Enter text">',
            'link': '<a href="#" class="link">Click here</a>'
        }
        
        # Test with real components
        test_results = self.validator.test_theme_with_real_components(
            generated_theme.css_content, component_samples
        )
        
        self.assertIsInstance(test_results, dict)
        self.assertIn('component_tests', test_results)
        self.assertIn('overall_rendering_score', test_results)
        self.assertIn('critical_failures', test_results)
        
        # Verify component tests
        component_tests = test_results['component_tests']
        self.assertEqual(len(component_tests), 3)
        
        for component_name, test_result in component_tests.items():
            self.assertIn(component_name, ['button', 'input', 'link'])
            self.assertIsInstance(test_result, dict)
            self.assertIn('component_name', test_result)
            self.assertIn('css_applied', test_result)
            self.assertIn('visual_issues', test_result)
            self.assertIn('functional_issues', test_result)
            self.assertIn('critical_failure', test_result)
        
        # Verify overall score
        overall_score = test_results['overall_rendering_score']
        self.assertIsInstance(overall_score, float)
        self.assertGreaterEqual(overall_score, 0.0)
        self.assertLessEqual(overall_score, 100.0)
        
        # Verify critical failures list
        critical_failures = test_results['critical_failures']
        self.assertIsInstance(critical_failures, list)


class UICompatibilityIntegrationTest(TestCase):
    """Integration tests for UI compatibility with the theming system."""
    
    def setUp(self):
        """Set up test data."""
        unique_id = str(uuid.uuid4())[:8]
        
        self.user = User.objects.create_user(
            email=f'test-integration-{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.event = Event.objects.create(
            title=f'Test Event {unique_id}',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
        
        self.validator = UICompatibilityValidator()
    
    def test_theme_validation_with_database_theme(self):
        """Test validation with a theme stored in the database."""
        # Create a theme in the database
        theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#ffffff',
            neutral_dark='#333333',
            css_content="""
            .button {
                background-color: #007bff;
                color: #ffffff;
                border: 1px solid #007bff;
                padding: 0.375rem 0.75rem;
                border-radius: 0.25rem;
            }
            .input {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 0.375rem 0.75rem;
            }
            """,
            css_hash='test-hash-' + str(uuid.uuid4())[:8],
            cache_key='test-cache-' + str(uuid.uuid4())[:8],
            wcag_compliant=True
        )
        
        # Validate the theme
        theme_colors = {
            'primary': theme.primary_color,
            'secondary': theme.secondary_color,
            'accent': theme.accent_color,
            'background': theme.neutral_light,
            'text': theme.neutral_dark
        }
        
        validation_results = self.validator.validate_complete_ui_compatibility(
            theme.css_content, theme_colors
        )
        
        # Should have good compatibility
        self.assertGreaterEqual(validation_results['overall_compatibility_score'], 60.0)
        
        # Should not have critical errors
        error_analysis = validation_results['error_analysis']
        critical_errors = [e for e in error_analysis.get('errors', []) 
                          if e.get('level') == 'critical']
        self.assertEqual(len(critical_errors), 0)
        
        # Clean up
        theme.delete()
    
    def test_validation_with_problematic_theme(self):
        """Test validation with a theme that has known issues."""
        # Create a problematic theme
        problematic_theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#000000',  # Black
            secondary_color='#111111',  # Very dark gray
            accent_color='#222222',  # Dark gray
            neutral_light='#000000',  # Black background
            neutral_dark='#333333',  # Dark text
            css_content="""
            .button {
                color: #333333;
                background-color: #000000;
                /* Poor contrast */
            }
            .input {
                /* Missing essential properties */
            }
            .broken {
                color: invalid-color;
                display: none;
                display: block;
            }
            """,
            css_hash='problematic-hash-' + str(uuid.uuid4())[:8],
            cache_key='problematic-cache-' + str(uuid.uuid4())[:8],
            wcag_compliant=False,
            is_fallback=False
        )
        
        # Validate the problematic theme
        theme_colors = {
            'primary': problematic_theme.primary_color,
            'secondary': problematic_theme.secondary_color,
            'accent': problematic_theme.accent_color,
            'background': problematic_theme.neutral_light,
            'text': problematic_theme.neutral_dark
        }
        
        validation_results = self.validator.validate_complete_ui_compatibility(
            problematic_theme.css_content, theme_colors
        )
        
        # Should detect issues
        self.assertTrue(validation_results['error_analysis']['errors_detected'])
        self.assertGreater(validation_results['error_analysis']['error_count'], 0)
        
        # Should provide recovery CSS
        recovery_css = validation_results['error_analysis']['recovery_css']
        self.assertGreater(len(recovery_css), 0)
        
        # Should provide recommendations
        recommendations = validation_results['recommendations']
        self.assertGreater(len(recommendations), 0)
        
        # Overall score should be lower due to issues
        self.assertLess(validation_results['overall_compatibility_score'], 80.0)
        
        # Clean up
        problematic_theme.delete()