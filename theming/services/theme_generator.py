"""
ThemeGenerator service for creating CSS themes from color palettes.

This module implements advanced theme generation using color theory,
accessibility validation, and responsive design for the Dynamic Event Theming System.
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import colorsys
import math
import re
from jinja2 import Template

logger = logging.getLogger(__name__)


@dataclass
class ColorVariations:
    """Color variations for interactive states."""
    base: str  # Base color
    light: str  # Lighter variant
    dark: str  # Darker variant
    hover: str  # Hover state
    active: str  # Active state
    focus: str  # Focus state
    disabled: str  # Disabled state


@dataclass
class GeneratedTheme:
    """Generated CSS theme with metadata."""
    css_content: str
    primary_variations: ColorVariations
    secondary_variations: ColorVariations
    accent_variations: ColorVariations
    neutral_variations: ColorVariations
    accessibility_compliant: bool
    contrast_adjustments_made: bool
    generation_metadata: Dict[str, Any]


class ThemeGenerator:
    """
    Advanced CSS theme generator using color theory and accessibility validation.
    
    Features:
    - Color palette to CSS variable conversion
    - Color variation generation (hover, active, disabled states)
    - Complementary color generation algorithms
    - CSS optimization and minification
    - WCAG accessibility compliance
    - Responsive design support
    """
    
    # CSS template for theme generation
    CSS_TEMPLATE = """
/* Dynamic Event Theme - Generated CSS */
:root {
    /* Primary Colors */
    --theme-primary: {{ primary_color }};
    --theme-primary-light: {{ primary_variations.light }};
    --theme-primary-dark: {{ primary_variations.dark }};
    --theme-primary-hover: {{ primary_variations.hover }};
    --theme-primary-active: {{ primary_variations.active }};
    --theme-primary-focus: {{ primary_variations.focus }};
    --theme-primary-disabled: {{ primary_variations.disabled }};
    
    /* Secondary Colors */
    --theme-secondary: {{ secondary_color }};
    --theme-secondary-light: {{ secondary_variations.light }};
    --theme-secondary-dark: {{ secondary_variations.dark }};
    --theme-secondary-hover: {{ secondary_variations.hover }};
    --theme-secondary-active: {{ secondary_variations.active }};
    --theme-secondary-focus: {{ secondary_variations.focus }};
    --theme-secondary-disabled: {{ secondary_variations.disabled }};
    
    /* Accent Colors */
    --theme-accent: {{ accent_color }};
    --theme-accent-light: {{ accent_variations.light }};
    --theme-accent-dark: {{ accent_variations.dark }};
    --theme-accent-hover: {{ accent_variations.hover }};
    --theme-accent-active: {{ accent_variations.active }};
    --theme-accent-focus: {{ accent_variations.focus }};
    --theme-accent-disabled: {{ accent_variations.disabled }};
    
    /* Neutral Colors */
    --theme-neutral-50: {{ neutral_variations.light }};
    --theme-neutral-100: {{ neutral_light }};
    --theme-neutral-200: {{ neutral_variations.base }};
    --theme-neutral-800: {{ neutral_variations.dark }};
    --theme-neutral-900: {{ neutral_dark }};
    
    /* Semantic Colors */
    --theme-success: {{ success_color }};
    --theme-warning: {{ warning_color }};
    --theme-error: {{ error_color }};
    --theme-info: {{ info_color }};
    
    /* Text Colors */
    --theme-text-primary: {{ text_primary }};
    --theme-text-secondary: {{ text_secondary }};
    --theme-text-muted: {{ text_muted }};
    --theme-text-inverse: {{ text_inverse }};
    
    /* Background Colors */
    --theme-bg-primary: {{ bg_primary }};
    --theme-bg-secondary: {{ bg_secondary }};
    --theme-bg-accent: {{ bg_accent }};
    
    /* Border Colors */
    --theme-border-light: {{ border_light }};
    --theme-border-medium: {{ border_medium }};
    --theme-border-dark: {{ border_dark }};
    
    /* Shadow Colors */
    --theme-shadow-light: {{ shadow_light }};
    --theme-shadow-medium: {{ shadow_medium }};
    --theme-shadow-dark: {{ shadow_dark }};
}

/* Component Styles */
.btn-primary {
    background-color: var(--theme-primary);
    border-color: var(--theme-primary);
    color: var(--theme-text-inverse);
}

.btn-primary:hover {
    background-color: var(--theme-primary-hover);
    border-color: var(--theme-primary-hover);
}

.btn-primary:active,
.btn-primary.active {
    background-color: var(--theme-primary-active);
    border-color: var(--theme-primary-active);
}

.btn-primary:focus,
.btn-primary.focus {
    box-shadow: 0 0 0 0.2rem var(--theme-primary-focus);
}

.btn-primary:disabled,
.btn-primary.disabled {
    background-color: var(--theme-primary-disabled);
    border-color: var(--theme-primary-disabled);
}

.btn-secondary {
    background-color: var(--theme-secondary);
    border-color: var(--theme-secondary);
    color: var(--theme-text-primary);
}

.btn-secondary:hover {
    background-color: var(--theme-secondary-hover);
    border-color: var(--theme-secondary-hover);
}

.btn-accent {
    background-color: var(--theme-accent);
    border-color: var(--theme-accent);
    color: var(--theme-text-inverse);
}

.btn-accent:hover {
    background-color: var(--theme-accent-hover);
    border-color: var(--theme-accent-hover);
}

/* Navigation */
.navbar-brand {
    color: var(--theme-primary) !important;
}

.nav-pills .nav-link.active {
    background-color: var(--theme-primary);
    color: var(--theme-text-inverse);
}

.nav-pills .nav-link:hover {
    background-color: var(--theme-primary-light);
}

/* Cards */
.card {
    border-color: var(--theme-border-light);
}

.card-header {
    background-color: var(--theme-bg-secondary);
    border-bottom-color: var(--theme-border-medium);
}

.card-primary {
    border-color: var(--theme-primary);
}

.card-primary .card-header {
    background-color: var(--theme-primary);
    color: var(--theme-text-inverse);
    border-bottom-color: var(--theme-primary-dark);
}

/* Forms */
.form-control:focus {
    border-color: var(--theme-primary);
    box-shadow: 0 0 0 0.2rem var(--theme-primary-focus);
}

.form-check-input:checked {
    background-color: var(--theme-primary);
    border-color: var(--theme-primary);
}

/* Alerts */
.alert-primary {
    color: var(--theme-primary-dark);
    background-color: var(--theme-primary-light);
    border-color: var(--theme-primary);
}

.alert-success {
    color: var(--theme-success);
    background-color: rgba(40, 167, 69, 0.1);
    border-color: var(--theme-success);
}

.alert-warning {
    color: var(--theme-warning);
    background-color: rgba(255, 193, 7, 0.1);
    border-color: var(--theme-warning);
}

.alert-error {
    color: var(--theme-error);
    background-color: rgba(220, 53, 69, 0.1);
    border-color: var(--theme-error);
}

/* Tables */
.table-primary {
    --bs-table-bg: var(--theme-primary-light);
    --bs-table-border-color: var(--theme-primary);
}

/* Badges */
.badge-primary {
    background-color: var(--theme-primary);
    color: var(--theme-text-inverse);
}

.badge-secondary {
    background-color: var(--theme-secondary);
    color: var(--theme-text-primary);
}

.badge-accent {
    background-color: var(--theme-accent);
    color: var(--theme-text-inverse);
}

/* Progress */
.progress-bar {
    background-color: var(--theme-primary);
}

/* Links */
a {
    color: var(--theme-primary);
}

a:hover {
    color: var(--theme-primary-hover);
}

/* Borders */
.border-primary {
    border-color: var(--theme-primary) !important;
}

.border-secondary {
    border-color: var(--theme-secondary) !important;
}

.border-accent {
    border-color: var(--theme-accent) !important;
}

/* Text Colors */
.text-primary {
    color: var(--theme-primary) !important;
}

.text-secondary {
    color: var(--theme-secondary) !important;
}

.text-accent {
    color: var(--theme-accent) !important;
}

.text-muted {
    color: var(--theme-text-muted) !important;
}

/* Background Colors */
.bg-primary {
    background-color: var(--theme-primary) !important;
    color: var(--theme-text-inverse) !important;
}

.bg-secondary {
    background-color: var(--theme-secondary) !important;
    color: var(--theme-text-primary) !important;
}

.bg-accent {
    background-color: var(--theme-accent) !important;
    color: var(--theme-text-inverse) !important;
}

.bg-light {
    background-color: var(--theme-bg-secondary) !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .btn {
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
    }
    
    .card {
        margin-bottom: 1rem;
    }
    
    .navbar-brand {
        font-size: 1.1rem;
    }
}

@media (max-width: 576px) {
    .btn {
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
    }
    
    .card-header {
        padding: 0.5rem 0.75rem;
    }
    
    .alert {
        padding: 0.5rem 0.75rem;
    }
}

/* High Contrast Mode Support */
@media (prefers-contrast: high) {
    :root {
        --theme-border-light: var(--theme-border-dark);
        --theme-shadow-light: var(--theme-shadow-dark);
    }
    
    .btn {
        border-width: 2px;
    }
    
    .form-control:focus {
        border-width: 2px;
    }
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
"""
    
    def __init__(self):
        """Initialize ThemeGenerator."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_theme(self, color_palette: Dict[str, str]) -> GeneratedTheme:
        """
        Generate complete CSS theme from color palette.
        
        Args:
            color_palette: Dictionary with primary, secondary, accent, neutral_light, neutral_dark colors
            
        Returns:
            GeneratedTheme with CSS content and metadata
        """
        try:
            # Extract base colors
            primary_color = color_palette.get('primary_color', '#007bff')
            secondary_color = color_palette.get('secondary_color', '#6c757d')
            accent_color = color_palette.get('accent_color', '#28a745')
            neutral_light = color_palette.get('neutral_light', '#f8f9fa')
            neutral_dark = color_palette.get('neutral_dark', '#343a40')
            
            # Generate color variations
            primary_variations = self.create_color_variations(primary_color)
            secondary_variations = self.create_color_variations(secondary_color)
            accent_variations = self.create_color_variations(accent_color)
            neutral_variations = self.create_color_variations('#e9ecef')  # Mid-gray
            
            # Generate semantic colors
            semantic_colors = self._generate_semantic_colors(primary_color, accent_color)
            
            # Generate text colors
            text_colors = self._generate_text_colors(primary_color, neutral_light, neutral_dark)
            
            # Generate background colors
            bg_colors = self._generate_background_colors(neutral_light, primary_color, accent_color)
            
            # Generate border colors
            border_colors = self._generate_border_colors(neutral_light, neutral_dark)
            
            # Generate shadow colors
            shadow_colors = self._generate_shadow_colors(neutral_dark)
            
            # Prepare template context
            context = {
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'accent_color': accent_color,
                'neutral_light': neutral_light,
                'neutral_dark': neutral_dark,
                'primary_variations': primary_variations,
                'secondary_variations': secondary_variations,
                'accent_variations': accent_variations,
                'neutral_variations': neutral_variations,
                **semantic_colors,
                **text_colors,
                **bg_colors,
                **border_colors,
                **shadow_colors,
            }
            
            # Generate CSS from template
            template = Template(self.CSS_TEMPLATE)
            css_content = template.render(**context)
            
            # Optimize CSS
            optimized_css = self.optimize_css(css_content)
            
            # Check accessibility compliance
            accessibility_compliant, adjustments_made = self._check_accessibility_compliance(color_palette)
            
            return GeneratedTheme(
                css_content=optimized_css,
                primary_variations=primary_variations,
                secondary_variations=secondary_variations,
                accent_variations=accent_variations,
                neutral_variations=neutral_variations,
                accessibility_compliant=accessibility_compliant,
                contrast_adjustments_made=adjustments_made,
                generation_metadata={
                    'colors_used': len(color_palette),
                    'variations_generated': 4,
                    'css_size_bytes': len(optimized_css),
                    'template_version': '1.0',
                    'responsive_breakpoints': 2,
                    'accessibility_features': ['high_contrast', 'reduced_motion'],
                }
            )
            
        except Exception as e:
            self.logger.error(f"Theme generation failed: {str(e)}")
            raise
    
    def create_color_variations(self, base_color: str) -> ColorVariations:
        """
        Generate color variations for interactive states.
        
        Args:
            base_color: Base hex color
            
        Returns:
            ColorVariations with all state colors
        """
        # Convert hex to RGB
        rgb = self._hex_to_rgb(base_color)
        
        # Convert to HSL for easier manipulation
        h, s, l = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        
        # Generate variations
        light = self._hsl_to_hex(h, s, min(1.0, l + 0.2))
        dark = self._hsl_to_hex(h, s, max(0.0, l - 0.2))
        hover = self._hsl_to_hex(h, s, max(0.0, l - 0.1))
        active = self._hsl_to_hex(h, s, max(0.0, l - 0.15))
        focus = self._add_alpha(base_color, 0.25)
        disabled = self._hsl_to_hex(h, max(0.0, s - 0.3), l + 0.1)
        
        return ColorVariations(
            base=base_color,
            light=light,
            dark=dark,
            hover=hover,
            active=active,
            focus=focus,
            disabled=disabled
        )
    
    def generate_complementary_colors(self, palette: Dict[str, str]) -> Dict[str, str]:
        """
        Create additional colors for complete theme.
        
        Args:
            palette: Base color palette
            
        Returns:
            Extended palette with complementary colors
        """
        primary = palette.get('primary_color', '#007bff')
        
        # Generate complementary colors using color theory
        primary_rgb = self._hex_to_rgb(primary)
        primary_hsl = colorsys.rgb_to_hls(primary_rgb[0]/255, primary_rgb[1]/255, primary_rgb[2]/255)
        
        # Complementary color (opposite on color wheel)
        comp_h = (primary_hsl[0] + 0.5) % 1.0
        complementary = self._hsl_to_hex(comp_h, primary_hsl[1], primary_hsl[2])
        
        # Triadic colors (120 degrees apart)
        triadic1_h = (primary_hsl[0] + 1/3) % 1.0
        triadic2_h = (primary_hsl[0] + 2/3) % 1.0
        triadic1 = self._hsl_to_hex(triadic1_h, primary_hsl[1], primary_hsl[2])
        triadic2 = self._hsl_to_hex(triadic2_h, primary_hsl[1], primary_hsl[2])
        
        # Analogous colors (30 degrees apart)
        analogous1_h = (primary_hsl[0] + 1/12) % 1.0
        analogous2_h = (primary_hsl[0] - 1/12) % 1.0
        analogous1 = self._hsl_to_hex(analogous1_h, primary_hsl[1], primary_hsl[2])
        analogous2 = self._hsl_to_hex(analogous2_h, primary_hsl[1], primary_hsl[2])
        
        extended_palette = palette.copy()
        extended_palette.update({
            'complementary': complementary,
            'triadic1': triadic1,
            'triadic2': triadic2,
            'analogous1': analogous1,
            'analogous2': analogous2,
        })
        
        return extended_palette
    
    def optimize_css(self, css_content: str) -> str:
        """
        Minify and optimize generated CSS.
        
        Args:
            css_content: Raw CSS content
            
        Returns:
            Optimized CSS string
        """
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove extra whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        
        # Remove whitespace around specific characters
        css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
        
        # Remove trailing semicolons before closing braces
        css_content = re.sub(r';\s*}', '}', css_content)
        
        # Remove empty rules
        css_content = re.sub(r'[^{}]+{\s*}', '', css_content)
        
        return css_content.strip()
    
    def _generate_semantic_colors(self, primary: str, accent: str) -> Dict[str, str]:
        """Generate semantic colors (success, warning, error, info)."""
        return {
            'success_color': '#28a745',  # Green
            'warning_color': '#ffc107',  # Yellow
            'error_color': '#dc3545',    # Red
            'info_color': primary,       # Use primary color for info
        }
    
    def _generate_text_colors(self, primary: str, light: str, dark: str) -> Dict[str, str]:
        """Generate text colors with proper contrast."""
        return {
            'text_primary': dark,
            'text_secondary': '#6c757d',
            'text_muted': '#adb5bd',
            'text_inverse': light,
        }
    
    def _generate_background_colors(self, light: str, primary: str, accent: str) -> Dict[str, str]:
        """Generate background colors."""
        return {
            'bg_primary': light,
            'bg_secondary': '#f8f9fa',
            'bg_accent': self._add_alpha(accent, 0.1),
        }
    
    def _generate_border_colors(self, light: str, dark: str) -> Dict[str, str]:
        """Generate border colors."""
        return {
            'border_light': '#e9ecef',
            'border_medium': '#dee2e6',
            'border_dark': '#adb5bd',
        }
    
    def _generate_shadow_colors(self, dark: str) -> Dict[str, str]:
        """Generate shadow colors."""
        return {
            'shadow_light': 'rgba(0, 0, 0, 0.1)',
            'shadow_medium': 'rgba(0, 0, 0, 0.15)',
            'shadow_dark': 'rgba(0, 0, 0, 0.25)',
        }
    
    def _check_accessibility_compliance(self, palette: Dict[str, str]) -> Tuple[bool, bool]:
        """
        Check if color palette meets accessibility standards.
        
        Returns:
            Tuple of (is_compliant, adjustments_made)
        """
        # Simplified accessibility check
        # In a real implementation, this would check contrast ratios
        primary = palette.get('primary_color', '#007bff')
        
        # Check if primary color has sufficient contrast with white text
        primary_rgb = self._hex_to_rgb(primary)
        luminance = self._calculate_luminance(primary_rgb)
        
        # WCAG AA requires 4.5:1 contrast ratio for normal text
        contrast_with_white = (1.0 + 0.05) / (luminance + 0.05)
        
        is_compliant = contrast_with_white >= 4.5
        adjustments_made = False
        
        return is_compliant, adjustments_made
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """Convert HSL to hex color."""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return self._rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))
    
    def _add_alpha(self, hex_color: str, alpha: float) -> str:
        """Add alpha channel to hex color (returns rgba)."""
        rgb = self._hex_to_rgb(hex_color)
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
    
    def _calculate_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """Calculate relative luminance for accessibility calculations."""
        def _linearize(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)
        
        r, g, b = rgb
        return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


# Utility functions
def generate_theme_from_colors(
    primary: str,
    secondary: str = '#6c757d',
    accent: str = '#28a745',
    neutral_light: str = '#f8f9fa',
    neutral_dark: str = '#343a40'
) -> GeneratedTheme:
    """
    Convenience function to generate theme from individual colors.
    
    Args:
        primary: Primary color hex
        secondary: Secondary color hex
        accent: Accent color hex
        neutral_light: Light neutral color hex
        neutral_dark: Dark neutral color hex
        
    Returns:
        GeneratedTheme with CSS content and metadata
    """
    generator = ThemeGenerator()
    palette = {
        'primary_color': primary,
        'secondary_color': secondary,
        'accent_color': accent,
        'neutral_light': neutral_light,
        'neutral_dark': neutral_dark,
    }
    return generator.generate_theme(palette)


def create_portal_specific_css(base_theme: GeneratedTheme, portal_type: str) -> str:
    """
    Generate portal-specific CSS overrides.
    
    Args:
        base_theme: Base generated theme
        portal_type: Type of portal ('staff', 'participant', 'organizer')
        
    Returns:
        Portal-specific CSS string
    """
    portal_customizations = {
        'staff': """
        /* Staff Portal Customizations */
        .staff-header {
            background: linear-gradient(135deg, var(--theme-primary), var(--theme-primary-dark));
            color: var(--theme-text-inverse);
        }
        
        .staff-sidebar {
            border-left: 3px solid var(--theme-accent);
            background-color: var(--theme-bg-secondary);
        }
        
        .staff-card {
            border-top: 4px solid var(--theme-primary);
        }
        
        .staff-badge {
            background-color: var(--theme-accent);
            color: var(--theme-text-inverse);
        }
        """,
        
        'participant': """
        /* Participant Portal Customizations */
        .participant-nav {
            background: linear-gradient(135deg, var(--theme-primary), var(--theme-accent));
            color: var(--theme-text-inverse);
        }
        
        .event-card {
            border-top: 4px solid var(--theme-primary);
            box-shadow: 0 2px 4px var(--theme-shadow-light);
        }
        
        .event-card:hover {
            box-shadow: 0 4px 8px var(--theme-shadow-medium);
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        .registration-button {
            background: linear-gradient(45deg, var(--theme-primary), var(--theme-accent));
            border: none;
            color: var(--theme-text-inverse);
        }
        
        .ticket-qr {
            border: 2px solid var(--theme-primary);
            border-radius: 8px;
        }
        """,
        
        'organizer': """
        /* Organizer Portal Customizations */
        .organizer-dashboard {
            background-color: var(--theme-bg-secondary);
        }
        
        .metric-card {
            border-left: 4px solid var(--theme-primary);
            background: linear-gradient(135deg, var(--theme-bg-primary), var(--theme-bg-secondary));
        }
        
        .metric-value {
            color: var(--theme-primary);
            font-weight: bold;
        }
        
        .chart-container {
            border: 1px solid var(--theme-border-light);
            border-radius: 8px;
            background-color: var(--theme-bg-primary);
        }
        
        .action-button {
            background-color: var(--theme-accent);
            color: var(--theme-text-inverse);
        }
        
        .action-button:hover {
            background-color: var(--theme-accent-hover);
        }
        """
    }
    
    return base_theme.css_content + portal_customizations.get(portal_type, '')