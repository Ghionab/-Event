"""
Visual Harmony and Branding Service

Implements gradient generation, hover effects, brand color prominence algorithms,
and functional element discoverability preservation for the theming system.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import colorsys
import math
from .advanced_color_processor import AdvancedColorProcessor, BrandColorHierarchy


@dataclass
class GradientDefinition:
    """Represents a CSS gradient definition."""
    type: str  # 'linear', 'radial', 'conic'
    direction: str
    color_stops: List[Tuple[str, float]]  # (color, position)
    css: str


@dataclass
class HoverEffects:
    """Represents hover effect definitions for UI elements."""
    primary_hover: str
    secondary_hover: str
    accent_hover: str
    button_hover: Dict[str, str]
    link_hover: Dict[str, str]


@dataclass
class BrandProminence:
    """Represents brand color prominence configuration."""
    header_colors: Dict[str, str]
    navigation_colors: Dict[str, str]
    cta_colors: Dict[str, str]  # Call-to-action
    accent_placement: List[str]


class VisualHarmonyService:
    """
    Service for creating visual harmony and branding elements.
    
    Generates gradients, hover effects, and maintains brand prominence
    while preserving functional element discoverability.
    """
    
    def __init__(self):
        self.color_processor = AdvancedColorProcessor()
    
    def generate_gradients(self, hierarchy: BrandColorHierarchy) -> List[GradientDefinition]:
        """
        Generate CSS gradients based on brand color hierarchy.
        
        Args:
            hierarchy: Brand color hierarchy from advanced color processor
            
        Returns:
            List of gradient definitions for various UI elements
        """
        gradients = []
        
        # Primary brand gradient (linear)
        if hierarchy.secondary_colors:
            primary_gradient = self._create_linear_gradient(
                hierarchy.primary_color,
                hierarchy.secondary_colors[0],
                direction="135deg"
            )
            gradients.append(primary_gradient)
        
        # Header gradient (horizontal)
        if len(hierarchy.secondary_colors) >= 2:
            header_gradient = self._create_linear_gradient(
                hierarchy.secondary_colors[0],
                hierarchy.secondary_colors[1],
                direction="90deg"
            )
            gradients.append(header_gradient)
        
        # Accent gradients for buttons and highlights
        for i, accent_color in enumerate(hierarchy.accent_colors[:2]):
            accent_gradient = self._create_radial_gradient(
                accent_color,
                self._lighten_color(accent_color, 0.1)
            )
            gradients.append(accent_gradient)
        
        # Advanced gradient variations
        gradients.extend(self._generate_advanced_gradients(hierarchy))
        
        return gradients
    
    def _generate_advanced_gradients(self, hierarchy: BrandColorHierarchy) -> List[GradientDefinition]:
        """Generate advanced gradient variations for sophisticated theming."""
        gradients = []
        
        # Multi-stop gradient using primary and accent colors
        if hierarchy.accent_colors:
            multi_stop = GradientDefinition(
                type='linear',
                direction='45deg',
                color_stops=[
                    (hierarchy.primary_color, 0.0),
                    (hierarchy.accent_colors[0], 0.5),
                    (self._darken_color(hierarchy.primary_color, 0.1), 1.0)
                ],
                css=f"linear-gradient(45deg, {hierarchy.primary_color} 0%, {hierarchy.accent_colors[0]} 50%, {self._darken_color(hierarchy.primary_color, 0.1)} 100%)"
            )
            gradients.append(multi_stop)
        
        # Subtle background gradient
        if hierarchy.neutral_colors:
            bg_gradient = self._create_linear_gradient(
                hierarchy.neutral_colors[0] if hierarchy.neutral_colors else '#f8f9fa',
                self._lighten_color(hierarchy.primary_color, 0.4),
                direction="180deg"
            )
            gradients.append(bg_gradient)
        
        # Conic gradient for special elements
        if len(hierarchy.secondary_colors) >= 2:
            conic_gradient = GradientDefinition(
                type='conic',
                direction='from 0deg',
                color_stops=[
                    (hierarchy.primary_color, 0.0),
                    (hierarchy.secondary_colors[0], 0.33),
                    (hierarchy.secondary_colors[1], 0.66),
                    (hierarchy.primary_color, 1.0)
                ],
                css=f"conic-gradient(from 0deg, {hierarchy.primary_color} 0%, {hierarchy.secondary_colors[0]} 33%, {hierarchy.secondary_colors[1]} 66%, {hierarchy.primary_color} 100%)"
            )
            gradients.append(conic_gradient)
        
        return gradients
    
    def generate_hover_effects(self, hierarchy: BrandColorHierarchy) -> HoverEffects:
        """Generate advanced hover effects based on brand colors."""
        return HoverEffects(
            primary_hover=self._generate_sophisticated_hover(hierarchy.primary_color),
            secondary_hover=self._generate_sophisticated_hover(
                hierarchy.secondary_colors[0] if hierarchy.secondary_colors else hierarchy.primary_color
            ),
            accent_hover=self._generate_sophisticated_hover(
                hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.primary_color
            ),
            button_hover=self._generate_button_hover_effects(hierarchy),
            link_hover=self._generate_link_hover_effects(hierarchy)
        )
    
    def _generate_sophisticated_hover(self, base_color: str) -> str:
        """Generate sophisticated hover effect for a color."""
        # Analyze color properties to determine best hover effect
        rgb = self._hex_to_rgb(base_color)
        hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        
        # For dark colors, lighten on hover
        if hsv[2] < 0.4:
            return self._lighten_color(base_color, 0.15)
        # For light colors, darken on hover
        elif hsv[2] > 0.7:
            return self._darken_color(base_color, 0.15)
        # For medium colors, increase saturation and slightly darken
        else:
            saturated = self._saturate_color(base_color, 0.1)
            return self._darken_color(saturated, 0.05)
    
    def _generate_button_hover_effects(self, hierarchy: BrandColorHierarchy) -> Dict[str, str]:
        """Generate comprehensive button hover effects."""
        return {
            'primary': self._generate_sophisticated_hover(hierarchy.primary_color),
            'primary_shadow': f"0 4px 8px {self._add_alpha(hierarchy.primary_color, 0.3)}",
            'secondary': self._generate_sophisticated_hover(
                hierarchy.secondary_colors[0] if hierarchy.secondary_colors else hierarchy.primary_color
            ),
            'secondary_shadow': f"0 2px 4px {self._add_alpha(hierarchy.secondary_colors[0] if hierarchy.secondary_colors else hierarchy.primary_color, 0.2)}",
            'accent': self._generate_sophisticated_hover(
                hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.primary_color
            ),
            'accent_glow': f"0 0 10px {self._add_alpha(hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.primary_color, 0.4)}",
            'outline': f"2px solid {hierarchy.primary_color}",
            'transform': 'translateY(-2px)',
            'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        }
    
    def _generate_link_hover_effects(self, hierarchy: BrandColorHierarchy) -> Dict[str, str]:
        """Generate sophisticated link hover effects."""
        primary_hover = self._generate_sophisticated_hover(hierarchy.primary_color)
        
        return {
            'color': primary_hover,
            'underline': hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.primary_color,
            'underline_thickness': '2px',
            'underline_offset': '3px',
            'transition': 'all 0.2s ease-in-out',
            'text_shadow': f"0 1px 2px {self._add_alpha(primary_hover, 0.2)}"
        }
    
    def calculate_brand_prominence(self, hierarchy: BrandColorHierarchy) -> BrandProminence:
        """Calculate optimal brand color placement for maximum prominence."""
        return BrandProminence(
            header_colors=self._generate_header_color_scheme(hierarchy),
            navigation_colors=self._generate_navigation_color_scheme(hierarchy),
            cta_colors=self._generate_cta_color_scheme(hierarchy),
            accent_placement=self._determine_optimal_accent_placement(hierarchy)
        )
    
    def _generate_header_color_scheme(self, hierarchy: BrandColorHierarchy) -> Dict[str, str]:
        """Generate optimal header color scheme."""
        primary_rgb = self._hex_to_rgb(hierarchy.primary_color)
        
        return {
            'background': hierarchy.primary_color,
            'background_gradient': f"linear-gradient(135deg, {hierarchy.primary_color}, {self._darken_color(hierarchy.primary_color, 0.1)})",
            'text': self._get_contrasting_text_color(hierarchy.primary_color),
            'accent': hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.secondary_colors[0] if hierarchy.secondary_colors else '#ffffff',
            'border': self._darken_color(hierarchy.primary_color, 0.2),
            'shadow': f"0 2px 4px {self._add_alpha(hierarchy.primary_color, 0.3)}"
        }
    
    def _generate_navigation_color_scheme(self, hierarchy: BrandColorHierarchy) -> Dict[str, str]:
        """Generate optimal navigation color scheme."""
        nav_base = hierarchy.secondary_colors[0] if hierarchy.secondary_colors else self._lighten_color(hierarchy.primary_color, 0.1)
        
        return {
            'background': nav_base,
            'text': self._get_contrasting_text_color(nav_base),
            'active': hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.primary_color,
            'active_text': self._get_contrasting_text_color(hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.primary_color),
            'hover': self._lighten_color(nav_base, 0.1),
            'border': self._darken_color(nav_base, 0.15),
            'indicator': hierarchy.primary_color
        }
    
    def _generate_cta_color_scheme(self, hierarchy: BrandColorHierarchy) -> Dict[str, str]:
        """Generate optimal call-to-action color scheme."""
        cta_primary = hierarchy.accent_colors[0] if hierarchy.accent_colors else hierarchy.primary_color
        
        return {
            'primary': cta_primary,
            'primary_text': self._get_contrasting_text_color(cta_primary),
            'primary_hover': self._generate_sophisticated_hover(cta_primary),
            'secondary': hierarchy.secondary_colors[0] if hierarchy.secondary_colors else self._lighten_color(hierarchy.primary_color, 0.2),
            'secondary_text': self._get_contrasting_text_color(hierarchy.secondary_colors[0] if hierarchy.secondary_colors else hierarchy.primary_color),
            'outline': hierarchy.primary_color,
            'outline_hover': self._generate_sophisticated_hover(hierarchy.primary_color),
            'shadow': f"0 4px 12px {self._add_alpha(cta_primary, 0.3)}",
            'glow': f"0 0 20px {self._add_alpha(cta_primary, 0.4)}"
        }
    
    def _determine_optimal_accent_placement(self, hierarchy: BrandColorHierarchy) -> List[str]:
        """Determine optimal placement for accent colors."""
        placements = ['buttons', 'links', 'highlights', 'borders']
        
        # Add more sophisticated placements based on color properties
        if hierarchy.accent_colors:
            accent_rgb = self._hex_to_rgb(hierarchy.accent_colors[0])
            accent_hsv = colorsys.rgb_to_hsv(accent_rgb[0]/255, accent_rgb[1]/255, accent_rgb[2]/255)
            
            # High saturation colors work well for focus states
            if accent_hsv[1] > 0.7:
                placements.extend(['focus_rings', 'active_states', 'progress_bars'])
            
            # Bright colors work well for notifications
            if accent_hsv[2] > 0.6:
                placements.extend(['notifications', 'badges', 'alerts'])
        
        return placements
    
    def _generate_sophisticated_hover(self, base_color: str) -> str:
        """Generate sophisticated hover effect (duplicate from hover effects for consistency)."""
        rgb = self._hex_to_rgb(base_color)
        hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        
        if hsv[2] < 0.4:
            return self._lighten_color(base_color, 0.15)
        elif hsv[2] > 0.7:
            return self._darken_color(base_color, 0.15)
        else:
            saturated = self._saturate_color(base_color, 0.1)
            return self._darken_color(saturated, 0.05)
    
    def preserve_functional_discoverability(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Ensure functional elements remain discoverable with brand colors."""
        preserved_colors = colors.copy()
        
        # Ensure sufficient contrast for interactive elements
        for element in ['button', 'link', 'input', 'select']:
            if element in preserved_colors:
                bg_color = preserved_colors.get(f'{element}_bg', '#ffffff')
                text_color = preserved_colors.get(f'{element}_text', preserved_colors[element])
                
                # Check and adjust contrast if needed
                if self._calculate_contrast_ratio(text_color, bg_color) < 4.5:
                    preserved_colors[f'{element}_text'] = self._get_contrasting_text_color(bg_color)
        
        return preserved_colors
    
    def _create_linear_gradient(self, color1: str, color2: str, direction: str = "135deg") -> GradientDefinition:
        """Create a linear gradient definition."""
        css = f"linear-gradient({direction}, {color1} 0%, {color2} 100%)"
        return GradientDefinition(
            type='linear',
            direction=direction,
            color_stops=[(color1, 0.0), (color2, 1.0)],
            css=css
        )
    
    def _create_radial_gradient(self, center_color: str, edge_color: str) -> GradientDefinition:
        """Create a radial gradient definition."""
        css = f"radial-gradient(circle, {center_color} 0%, {edge_color} 100%)"
        return GradientDefinition(
            type='radial',
            direction='circle',
            color_stops=[(center_color, 0.0), (edge_color, 1.0)],
            css=css
        )
    
    def _lighten_color(self, hex_color: str, amount: float) -> str:
        """Lighten a color by the specified amount."""
        rgb = self._hex_to_rgb(hex_color)
        hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        new_hsv = (hsv[0], hsv[1], min(1.0, hsv[2] + amount))
        new_rgb = colorsys.hsv_to_rgb(*new_hsv)
        return f"#{int(new_rgb[0]*255):02x}{int(new_rgb[1]*255):02x}{int(new_rgb[2]*255):02x}"
    
    def _darken_color(self, hex_color: str, amount: float) -> str:
        """Darken a color by the specified amount."""
        rgb = self._hex_to_rgb(hex_color)
        hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        new_hsv = (hsv[0], hsv[1], max(0.0, hsv[2] - amount))
        new_rgb = colorsys.hsv_to_rgb(*new_hsv)
        return f"#{int(new_rgb[0]*255):02x}{int(new_rgb[1]*255):02x}{int(new_rgb[2]*255):02x}"
    
    def _saturate_color(self, hex_color: str, amount: float) -> str:
        """Increase saturation of a color."""
        rgb = self._hex_to_rgb(hex_color)
        hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        new_hsv = (hsv[0], min(1.0, hsv[1] + amount), hsv[2])
        new_rgb = colorsys.hsv_to_rgb(*new_hsv)
        return f"#{int(new_rgb[0]*255):02x}{int(new_rgb[1]*255):02x}{int(new_rgb[2]*255):02x}"
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _get_contrasting_text_color(self, bg_color: str) -> str:
        """Get contrasting text color (black or white) for background."""
        rgb = self._hex_to_rgb(bg_color)
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        return '#000000' if luminance > 0.5 else '#ffffff'
    
    def _add_alpha(self, hex_color: str, alpha: float) -> str:
        """Add alpha channel to hex color (returns rgba)."""
        rgb = self._hex_to_rgb(hex_color)
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
    
    def _add_alpha(self, hex_color: str, alpha: float) -> str:
        """Add alpha channel to hex color (returns rgba)."""
        rgb = self._hex_to_rgb(hex_color)
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
        """Calculate WCAG contrast ratio between two colors."""
        def luminance(hex_color):
            rgb = self._hex_to_rgb(hex_color)
            r, g, b = [x/255.0 for x in rgb]
            r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
            g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
            b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
            return 0.2126*r + 0.7152*g + 0.0722*b
        
        l1 = luminance(color1)
        l2 = luminance(color2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)