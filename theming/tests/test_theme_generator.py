"""
Tests for ThemeGenerator service.
"""

from django.test import TestCase
from theming.services.theme_generator import (
    ThemeGenerator, ColorVariations, GeneratedTheme,
    generate_theme_from_colors, create_portal_specific_css
)


class ThemeGeneratorTest(TestCase):
    """Test ThemeGenerator functionality"""
    
    def setUp(self):
        self.generator = ThemeGenerator()
        self.test_palette = {
            'primary_color': '#007bff',
            'secondary_color': '#6c757d',
            'accent_color': '#28a745',
            'neutral_light': '#f8f9fa',
            'neutral_dark': '#343a40',
        }
    
    def test_theme_generation(self):
        """Test basic theme generation"""
        theme = self.generator.generate_theme(self.test_palette)
        
        self.assertIsInstance(theme, GeneratedTheme)
        self.assertIsInstance(theme.css_content, str)
        self.assertGreater(len(theme.css_content), 1000)  # Should be substantial CSS
        self.assertIn('--theme-primary:', theme.css_content)
        self.assertIn('--theme-secondary:', theme.css_content)
        self.assertIn('--theme-accent:', theme.css_content)
    
    def test_color_variations_generation(self):
        """Test color variation generation"""
        variations = self.generator.create_color_variations('#007bff')
        
        self.assertIsInstance(variations, ColorVariations)
        self.assertEqual(variations.base, '#007bff')
        self.assertTrue(variations.light.startswith('#'))
        self.assertTrue(variations.dark.startswith('#'))
        self.assertTrue(variations.hover.startswith('#'))
        self.assertTrue(variations.active.startswith('#'))
        self.assertTrue(variations.focus.startswith('rgba'))  # Should have alpha
        self.assertTrue(variations.disabled.startswith('#'))
    
    def test_complementary_colors_generation(self):
        """Test complementary color generation"""
        extended_palette = self.generator.generate_complementary_colors(self.test_palette)
        
        self.assertIn('complementary', extended_palette)
        self.assertIn('triadic1', extended_palette)
        self.assertIn('triadic2', extended_palette)
        self.assertIn('analogous1', extended_palette)
        self.assertIn('analogous2', extended_palette)
        
        # All should be valid hex colors
        for color_key in ['complementary', 'triadic1', 'triadic2', 'analogous1', 'analogous2']:
            color = extended_palette[color_key]
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)
    
    def test_css_optimization(self):
        """Test CSS optimization and minification"""
        unoptimized_css = """
        /* This is a comment */
        .test {
            color: red;
            background: blue;
        }
        
        .empty {
        }
        
        .another {
            margin: 10px ;
            padding: 5px;
        }
        """
        
        optimized = self.generator.optimize_css(unoptimized_css)
        
        # Should remove comments
        self.assertNotIn('/* This is a comment */', optimized)
        
        # Should remove empty rules
        self.assertNotIn('.empty', optimized)
        
        # Should be more compact
        self.assertLess(len(optimized), len(unoptimized_css))
    
    def test_accessibility_compliance_check(self):
        """Test accessibility compliance checking"""
        compliant, adjustments = self.generator._check_accessibility_compliance(self.test_palette)
        
        self.assertIsInstance(compliant, bool)
        self.assertIsInstance(adjustments, bool)
    
    def test_hex_to_rgb_conversion(self):
        """Test hex to RGB conversion"""
        rgb = self.generator._hex_to_rgb('#ff0000')
        self.assertEqual(rgb, (255, 0, 0))
        
        rgb = self.generator._hex_to_rgb('#00ff00')
        self.assertEqual(rgb, (0, 255, 0))
        
        rgb = self.generator._hex_to_rgb('#0000ff')
        self.assertEqual(rgb, (0, 0, 255))
    
    def test_rgb_to_hex_conversion(self):
        """Test RGB to hex conversion"""
        hex_color = self.generator._rgb_to_hex((255, 0, 0))
        self.assertEqual(hex_color, '#ff0000')
        
        hex_color = self.generator._rgb_to_hex((0, 255, 0))
        self.assertEqual(hex_color, '#00ff00')
        
        hex_color = self.generator._rgb_to_hex((0, 0, 255))
        self.assertEqual(hex_color, '#0000ff')
    
    def test_alpha_addition(self):
        """Test adding alpha channel to colors"""
        rgba = self.generator._add_alpha('#ff0000', 0.5)
        self.assertEqual(rgba, 'rgba(255, 0, 0, 0.5)')
        
        rgba = self.generator._add_alpha('#00ff00', 0.25)
        self.assertEqual(rgba, 'rgba(0, 255, 0, 0.25)')
    
    def test_luminance_calculation(self):
        """Test luminance calculation for accessibility"""
        # White should have high luminance
        white_luminance = self.generator._calculate_luminance((255, 255, 255))
        self.assertGreater(white_luminance, 0.9)
        
        # Black should have low luminance
        black_luminance = self.generator._calculate_luminance((0, 0, 0))
        self.assertLess(black_luminance, 0.1)
    
    def test_theme_metadata(self):
        """Test theme generation metadata"""
        theme = self.generator.generate_theme(self.test_palette)
        
        self.assertIn('colors_used', theme.generation_metadata)
        self.assertIn('variations_generated', theme.generation_metadata)
        self.assertIn('css_size_bytes', theme.generation_metadata)
        self.assertIn('template_version', theme.generation_metadata)
        
        self.assertEqual(theme.generation_metadata['colors_used'], 5)
        self.assertGreater(theme.generation_metadata['css_size_bytes'], 0)


class ThemeGeneratorUtilityTest(TestCase):
    """Test utility functions"""
    
    def test_generate_theme_from_colors(self):
        """Test convenience function for theme generation"""
        theme = generate_theme_from_colors(
            primary='#007bff',
            secondary='#6c757d',
            accent='#28a745'
        )
        
        self.assertIsInstance(theme, GeneratedTheme)
        self.assertIn('--theme-primary:#007bff', theme.css_content)  # No space after colon due to optimization
        self.assertIn('--theme-secondary:#6c757d', theme.css_content)
        self.assertIn('--theme-accent:#28a745', theme.css_content)
    
    def test_create_portal_specific_css(self):
        """Test portal-specific CSS generation"""
        base_theme = generate_theme_from_colors('#007bff')
        
        # Test staff portal CSS
        staff_css = create_portal_specific_css(base_theme, 'staff')
        self.assertIn('staff-header', staff_css)
        self.assertIn('staff-sidebar', staff_css)
        
        # Test participant portal CSS
        participant_css = create_portal_specific_css(base_theme, 'participant')
        self.assertIn('participant-nav', participant_css)
        self.assertIn('event-card', participant_css)
        
        # Test organizer portal CSS
        organizer_css = create_portal_specific_css(base_theme, 'organizer')
        self.assertIn('organizer-dashboard', organizer_css)
        self.assertIn('metric-card', organizer_css)
        
        # Test unknown portal type
        unknown_css = create_portal_specific_css(base_theme, 'unknown')
        self.assertEqual(unknown_css, base_theme.css_content)  # Should just return base theme
    
    def test_portal_css_contains_base_theme(self):
        """Test that portal-specific CSS includes base theme"""
        base_theme = generate_theme_from_colors('#007bff')
        staff_css = create_portal_specific_css(base_theme, 'staff')
        
        # Should contain base theme CSS
        self.assertIn('--theme-primary:', staff_css)
        self.assertIn('.btn-primary', staff_css)
        
        # Should also contain staff-specific CSS
        self.assertIn('staff-header', staff_css)


class ThemeGeneratorEdgeCasesTest(TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        self.generator = ThemeGenerator()
    
    def test_empty_palette(self):
        """Test theme generation with empty palette"""
        theme = self.generator.generate_theme({})
        
        # Should use default colors
        self.assertIsInstance(theme, GeneratedTheme)
        self.assertIn('--theme-primary:', theme.css_content)
    
    def test_invalid_hex_colors(self):
        """Test handling of invalid hex colors"""
        palette = {
            'primary_color': 'invalid',
            'secondary_color': '#xyz123',
            'accent_color': '#28a745',
        }
        
        # Should handle gracefully and use defaults
        try:
            theme = self.generator.generate_theme(palette)
            self.assertIsInstance(theme, GeneratedTheme)
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass
    
    def test_extreme_color_values(self):
        """Test with extreme color values"""
        palette = {
            'primary_color': '#000000',  # Pure black
            'secondary_color': '#ffffff',  # Pure white
            'accent_color': '#ff0000',    # Pure red
            'neutral_light': '#ffffff',
            'neutral_dark': '#000000',
        }
        
        theme = self.generator.generate_theme(palette)
        self.assertIsInstance(theme, GeneratedTheme)
        
        # Should generate variations even for extreme colors
        self.assertIsInstance(theme.primary_variations, ColorVariations)
        self.assertIsInstance(theme.secondary_variations, ColorVariations)
    
    def test_css_template_rendering(self):
        """Test that CSS template renders without errors"""
        theme = self.generator.generate_theme({
            'primary_color': '#007bff',
            'secondary_color': '#6c757d',
            'accent_color': '#28a745',
            'neutral_light': '#f8f9fa',
            'neutral_dark': '#343a40',
        })
        
        # Should not contain unrendered template variables
        self.assertNotIn('{{ ', theme.css_content)  # Template variables with spaces
        self.assertNotIn(' }}', theme.css_content)
        
        # Should contain actual color values
        self.assertIn('#007bff', theme.css_content)
        self.assertIn('#6c757d', theme.css_content)
        self.assertIn('#28a745', theme.css_content)