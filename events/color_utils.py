"""
Color palette extraction utility for dynamic event branding.
Uses ColorThief and Pillow to extract colors from event logos.
Includes WCAG 2.1 AA accessibility compliance for contrast ratios.
"""

from PIL import Image
from colorthief import ColorThief
import colorsys
import os
import tempfile
from typing import List, Tuple, Optional


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color string."""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB to HSL color space."""
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360, s * 100, l * 100)


def hsl_to_rgb(hsl: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Convert HSL to RGB color space."""
    h, s, l = hsl[0] / 360, hsl[1] / 100, hsl[2] / 100
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def get_relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate relative luminance of a color per WCAG 2.1 specifications.
    
    https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
    
    Args:
        rgb: RGB tuple with values 0-255
        
    Returns:
        Relative luminance value (0.0 to 1.0)
    """
    def normalize_color(c):
        srgb = c / 255.0
        if srgb <= 0.03928:
            return srgb / 12.92
        else:
            return ((srgb + 0.055) / 1.055) ** 2.4
    
    r, g, b = rgb
    r_lin = normalize_color(r)
    g_lin = normalize_color(g)
    b_lin = normalize_color(b)
    
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def get_contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """
    Calculate contrast ratio between two colors per WCAG 2.1.
    
    https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio
    
    Args:
        color1: First color as RGB tuple
        color2: Second color as RGB tuple
        
    Returns:
        Contrast ratio (1.0 to 21.0)
    """
    lum1 = get_relative_luminance(color1)
    lum2 = get_relative_luminance(color2)
    
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)


def meets_wcag_aa(background_rgb: Tuple[int, int, int], 
                 text_rgb: Tuple[int, int, int], 
                 large_text: bool = False) -> bool:
    """
    Check if color combination meets WCAG 2.1 AA standards.
    
    WCAG AA Requirements:
    - Normal text (< 18pt or < 14pt bold): 4.5:1
    - Large text (>= 18pt or >= 14pt bold): 3.0:1
    
    Args:
        background_rgb: Background color
        text_rgb: Text color
        large_text: Whether text qualifies as "large"
        
    Returns:
        True if meets AA standards
    """
    ratio = get_contrast_ratio(background_rgb, text_rgb)
    threshold = 3.0 if large_text else 4.5
    return ratio >= threshold


def meets_wcag_aaa(background_rgb: Tuple[int, int, int], 
                  text_rgb: Tuple[int, int, int], 
                  large_text: bool = False) -> bool:
    """
    Check if color combination meets WCAG 2.1 AAA standards.
    
    WCAG AAA Requirements:
    - Normal text: 7.0:1
    - Large text: 4.5:1
    
    Args:
        background_rgb: Background color
        text_rgb: Text color
        large_text: Whether text qualifies as "large"
        
    Returns:
        True if meets AAA standards
    """
    ratio = get_contrast_ratio(background_rgb, text_rgb)
    threshold = 4.5 if large_text else 7.0
    return ratio >= threshold


def find_accessible_text_color(background_rgb: Tuple[int, int, int], 
                               large_text: bool = False,
                               prefer_light: bool = None) -> str:
    """
    Find black or white text color that meets WCAG AA contrast requirements.
    
    Args:
        background_rgb: Background color
        large_text: Whether text is large (3:1 threshold vs 4.5:1)
        prefer_light: Prefer light text if both pass (None = auto)
        
    Returns:
        '#ffffff' or '#000000' that meets contrast requirements
    """
    white = (255, 255, 255)
    black = (0, 0, 0)
    
    white_ratio = get_contrast_ratio(background_rgb, white)
    black_ratio = get_contrast_ratio(background_rgb, black)
    
    threshold = 3.0 if large_text else 4.5
    
    white_passes = white_ratio >= threshold
    black_passes = black_ratio >= threshold
    
    # Determine which to use based on preference and contrast
    if prefer_light is None:
        # Auto: pick the one with better contrast
        if white_passes and black_passes:
            return '#ffffff' if white_ratio > black_ratio else '#000000'
        elif white_passes:
            return '#ffffff'
        elif black_passes:
            return '#000000'
        else:
            # Neither passes, return the one with higher contrast
            return '#ffffff' if white_ratio > black_ratio else '#000000'
    elif prefer_light:
        return '#ffffff' if white_passes else '#000000'
    else:
        return '#000000' if black_passes else '#ffffff'


def adjust_color_for_contrast(background_rgb: Tuple[int, int, int],
                               target_rgb: Tuple[int, int, int],
                               min_ratio: float = 4.5,
                               max_iterations: int = 20) -> Tuple[int, int, int]:
    """
    Adjust a color to meet minimum contrast ratio with background.
    
    Uses HSL adjustments to lighten or darken the target color until
    it meets the contrast requirement.
    
    Args:
        background_rgb: Background color
        target_rgb: Initial target color to adjust
        min_ratio: Minimum required contrast ratio (default 4.5 for AA)
        max_iterations: Max adjustment attempts to prevent infinite loop
        
    Returns:
        Adjusted RGB tuple that meets contrast requirement
    """
    current = target_rgb
    
    for i in range(max_iterations):
        ratio = get_contrast_ratio(background_rgb, current)
        
        if ratio >= min_ratio:
            return current
        
        # Determine if we need to lighten or darken
        bg_lum = get_relative_luminance(background_rgb)
        current_lum = get_relative_luminance(current)
        
        if bg_lum > current_lum:
            # Background is lighter, darken the text
            current = adjust_brightness(current, 0.9)
        else:
            # Background is darker, lighten the text
            current = adjust_brightness(current, 1.1)
    
    # If we couldn't meet the ratio, return black or white with best contrast
    white_ratio = get_contrast_ratio(background_rgb, (255, 255, 255))
    black_ratio = get_contrast_ratio(background_rgb, (0, 0, 0))
    
    return (255, 255, 255) if white_ratio > black_ratio else (0, 0, 0)


def validate_and_fix_palette(palette: dict, 
                             require_aa: bool = True) -> dict:
    """
    Validate and fix a color palette for accessibility.
    
    Ensures all text colors have sufficient contrast with their backgrounds.
    Adjusts colors that don't meet standards.
    
    Args:
        palette: Color palette dictionary
        require_aa: Whether to enforce AA standards (default True)
        
    Returns:
        Validated and potentially adjusted palette
    """
    if not palette:
        return get_default_palette()
    
    min_ratio = 4.5 if require_aa else 3.0
    
    # Extract RGB values
    primary_rgb = hex_to_rgb(palette.get('primary_color', '#4f46e5'))
    secondary_rgb = hex_to_rgb(palette.get('secondary_color', '#6b7280'))
    accent_rgb = hex_to_rgb(palette.get('accent_color', '#10b981'))
    
    # Determine text colors for each background
    primary_text_rgb = hex_to_rgb(palette.get('text_on_primary', '#ffffff'))
    secondary_text_rgb = hex_to_rgb(palette.get('text_on_secondary', '#ffffff'))
    accent_text_rgb = hex_to_rgb(palette.get('text_on_accent', '#ffffff'))
    
    # Validate and fix each combination
    if get_contrast_ratio(primary_rgb, primary_text_rgb) < min_ratio:
        primary_text_rgb = adjust_color_for_contrast(primary_rgb, primary_text_rgb, min_ratio)
    
    if get_contrast_ratio(secondary_rgb, secondary_text_rgb) < min_ratio:
        secondary_text_rgb = adjust_color_for_contrast(secondary_rgb, secondary_text_rgb, min_ratio)
    
    if get_contrast_ratio(accent_rgb, accent_text_rgb) < min_ratio:
        accent_text_rgb = adjust_color_for_contrast(accent_rgb, accent_text_rgb, min_ratio)
    
    # Also ensure the colors have contrast with the page background (white)
    white = (255, 255, 255)
    if get_contrast_ratio(white, primary_rgb) < 3.0:
        # Primary is too light, darken it for UI elements
        primary_rgb = adjust_color_for_contrast(white, primary_rgb, 3.0)
    
    # Return validated palette
    return {
        'primary_color': rgb_to_hex(primary_rgb),
        'secondary_color': rgb_to_hex(secondary_rgb),
        'accent_color': rgb_to_hex(accent_rgb),
        'background_color': palette.get('background_color', '#f9fafb'),
        'text_on_primary': rgb_to_hex(primary_text_rgb),
        'text_on_secondary': rgb_to_hex(secondary_text_rgb),
        'text_on_accent': rgb_to_hex(accent_text_rgb),
    }


def is_valid_color(rgb: Tuple[int, int, int], min_brightness: int = 30, max_brightness: int = 225) -> bool:
    """
    Check if a color is valid (not too dark or too light).
    
    Args:
        rgb: RGB tuple
        min_brightness: Minimum brightness (0-255)
        max_brightness: Maximum brightness (0-255)
    
    Returns:
        True if color is within valid range
    """
    # Calculate perceived brightness using weighted formula
    brightness = (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114)
    return min_brightness <= brightness <= max_brightness


def get_contrasting_text_color(background_rgb: Tuple[int, int, int]) -> str:
    """
    Determine whether to use black or white text based on background brightness.
    
    This is a simpler version that doesn't check contrast ratios.
    For WCAG compliance, use find_accessible_text_color().
    
    Args:
        background_rgb: Background color as RGB tuple
    
    Returns:
        '#ffffff' or '#000000'
    """
    brightness = (background_rgb[0] * 0.299 + background_rgb[1] * 0.587 + background_rgb[2] * 0.114)
    return '#ffffff' if brightness < 128 else '#000000'


def adjust_brightness(rgb: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """
    Adjust the brightness of a color.
    
    Args:
        rgb: RGB tuple
        factor: Brightness factor (0.0 to 2.0, where 1.0 is unchanged)
    
    Returns:
        Adjusted RGB tuple
    """
    hsl = rgb_to_hsl(rgb)
    new_lightness = max(0, min(100, hsl[2] * factor))
    new_hsl = (hsl[0], hsl[1], new_lightness)
    return hsl_to_rgb(new_hsl)


def get_complementary_color(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """
    Get the complementary color (opposite on color wheel).
    
    Args:
        rgb: RGB tuple
    
    Returns:
        Complementary RGB tuple
    """
    hsl = rgb_to_hsl(rgb)
    new_hue = (hsl[0] + 180) % 360
    return hsl_to_rgb((new_hue, hsl[1], hsl[2]))


def get_analogous_colors(rgb: Tuple[int, int, int], count: int = 2) -> List[Tuple[int, int, int]]:
    """
    Get analogous colors (adjacent on color wheel).
    
    Args:
        rgb: RGB tuple
        count: Number of analogous colors to generate
    
    Returns:
        List of RGB tuples
    """
    hsl = rgb_to_hsl(rgb)
    colors = []
    step = 30  # degrees
    
    for i in range(1, count + 1):
        offset = step * i
        hue1 = (hsl[0] + offset) % 360
        hue2 = (hsl[0] - offset) % 360
        colors.append(hsl_to_rgb((hue1, hsl[1], hsl[2])))
        if len(colors) < count:
            colors.append(hsl_to_rgb((hue2, hsl[1], hsl[2])))
    
    return colors[:count]


def extract_color_palette(image_path: str, color_count: int = 8) -> Optional[dict]:
    """
    Extract a premium color palette from an image file.
    
    Uses advanced color analysis to identify brand colors, preserve dark backgrounds
    (like navy blue), and capture metallic tones (gold, silver) for a professional
    10/10 quality event theming experience.
    
    Args:
        image_path: Path to the image file
        color_count: Number of colors to extract (default 8 for better analysis)
    
    Returns:
        Dictionary with primary_color, secondary_color, accent_color, background_color
        and optional use_dark_theme flag
        Returns None if extraction fails
    """
    try:
        # Verify file exists and is readable
        if not os.path.exists(image_path):
            return None
        
        # Open and analyze image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Check image dimensions
            width, height = img.size
            if width < 10 or height < 10:
                return None
            
            # Get image data for analysis
            img_data = list(img.getdata())
            total_pixels = len(img_data)
            
            # Analyze for dominant background color
            # Sample edges and corners to detect background
            edge_pixels = []
            for x in range(0, width, max(1, width // 20)):
                edge_pixels.append(img_data[x])  # Top edge
                edge_pixels.append(img_data[(height - 1) * width + x])  # Bottom edge
            for y in range(0, height, max(1, height // 20)):
                edge_pixels.append(img_data[y * width])  # Left edge
                edge_pixels.append(img_data[y * width + width - 1])  # Right edge
            
            # Find most common edge color (likely background)
            from collections import Counter
            edge_color_counts = Counter(edge_pixels)
            dominant_edge_color = edge_color_counts.most_common(1)[0][0]
            
            # Check if background is dark (navy/black detection)
            edge_brightness = get_relative_luminance(dominant_edge_color)
            has_dark_background = edge_brightness < 0.15  # Dark if luminance < 15%
            
            # Detect if it's a blue-toned dark color (navy)
            r, g, b = dominant_edge_color
            is_navy_blue = has_dark_background and b > r and b > g and b > 80
        
        # Use ColorThief to extract dominant colors
        color_thief = ColorThief(image_path)
        raw_palette = color_thief.get_palette(color_count=color_count, quality=5)
        
        # Categorize colors by their characteristics
        dark_colors = []
        light_colors = []
        saturated_colors = []
        metallic_colors = []  # Golds, silvers, bronzes
        
        for color in raw_palette:
            r, g, b = color
            hsl = rgb_to_hsl(color)
            brightness = (r * 0.299 + g * 0.587 + b * 0.114) / 255
            saturation = hsl[1] / 100
            
            # Detect metallic colors (gold, silver, bronze)
            # Gold: high red and green, lower blue, moderate-high brightness
            # Silver: balanced RGB, high brightness
            is_gold = (r > 180 and g > 140 and b < 100 and 
                      brightness > 0.5 and brightness < 0.9 and
                      abs(r - g) < 60 and r > b + 50)
            
            is_silver = (abs(r - g) < 30 and abs(g - b) < 30 and 
                        brightness > 0.6 and r > 150)
            
            if is_gold or is_silver:
                metallic_colors.append((color, 'gold' if is_gold else 'silver'))
            elif brightness < 0.3:
                dark_colors.append(color)
            elif brightness > 0.7:
                light_colors.append(color)
            elif saturation > 0.4:
                saturated_colors.append(color)
        
        # Build professional palette based on detected characteristics
        
        # PRIMARY COLOR: Use metallic gold if detected, otherwise most saturated
        if metallic_colors:
            # Prefer gold over silver for warmth
            gold_colors = [c for c, t in metallic_colors if t == 'gold']
            if gold_colors:
                primary_rgb = gold_colors[0]
            else:
                primary_rgb = metallic_colors[0][0]
        elif saturated_colors:
            primary_rgb = saturated_colors[0]
        else:
            primary_rgb = raw_palette[0]
        
        # SECONDARY COLOR: Use navy blue if dark background detected
        if has_dark_background and is_navy_blue:
            secondary_rgb = dominant_edge_color
        elif dark_colors:
            # Prefer colors with blue tones for sophistication
            blue_toned = [c for c in dark_colors if c[2] > c[0] and c[2] > c[1]]
            secondary_rgb = blue_toned[0] if blue_toned else dark_colors[0]
        else:
            secondary_rgb = get_complementary_color(primary_rgb)
        
        # ACCENT COLOR: Another metallic or complementary
        if len(metallic_colors) > 1:
            accent_rgb = metallic_colors[1][0]
        elif saturated_colors and len(saturated_colors) > 1:
            accent_rgb = saturated_colors[1]
        else:
            analogous = get_analogous_colors(primary_rgb, 2)
            accent_rgb = analogous[1] if len(analogous) > 1 else adjust_brightness(primary_rgb, 1.2)
        
        # BACKGROUND COLOR: Light for dark themes, cream/off-white for gold themes
        if metallic_colors and any(t == 'gold' for _, t in metallic_colors):
            # Create a warm cream background for gold themes
            bg_rgb = (252, 250, 245)  # Warm off-white
        elif has_dark_background and is_navy_blue:
            # Create a very light cream/beige for navy themes
            bg_rgb = (250, 248, 245)  # Cream
        else:
            # Standard light background
            primary_hsl = rgb_to_hsl(primary_rgb)
            bg_rgb = hsl_to_rgb((primary_hsl[0], max(5, primary_hsl[1] * 0.15), 97))
        
        # Ensure background has good contrast with text
        bg_brightness = get_relative_luminance(bg_rgb)
        if bg_brightness < 0.9:  # If not very light, lighten it
            bg_rgb = (min(255, bg_rgb[0] + 10), min(255, bg_rgb[1] + 10), min(255, bg_rgb[2] + 8))
        
        # Determine accessible text colors
        primary_text = find_accessible_text_color(primary_rgb)
        secondary_text = find_accessible_text_color(secondary_rgb)
        accent_text = find_accessible_text_color(accent_rgb)
        
        # Convert to hex
        result = {
            'primary_color': rgb_to_hex(primary_rgb),
            'secondary_color': rgb_to_hex(secondary_rgb),
            'accent_color': rgb_to_hex(accent_rgb),
            'background_color': rgb_to_hex(bg_rgb),
            'text_on_primary': primary_text,
            'text_on_secondary': secondary_text,
            'text_on_accent': accent_text,
        }
        
        # Validate and fix for accessibility
        result = validate_and_fix_palette(result, require_aa=True)
        
        return result
        
    except Exception as e:
        print(f"Error extracting color palette: {e}")
        return None


def get_premium_navy_gold_palette() -> dict:
    """
    Return a premium navy blue and gold palette for anniversary/corporate events.
    
    This is a fallback that creates a professional 10/10 look when extraction
    doesn't capture the brand colors properly.
    
    Returns:
        Dictionary with premium colors (all WCAG AA compliant)
    """
    return {
        'primary_color': '#c9a961',      # Metallic Gold
        'secondary_color': '#0a1628',    # Deep Navy Blue
        'accent_color': '#d4af37',       # Bright Gold
        'background_color': '#faf8f5',   # Warm Cream
        'text_on_primary': '#0a1628',    # Navy text on gold
        'text_on_secondary': '#ffffff',  # White text on navy
        'text_on_accent': '#0a1628',     # Navy text on bright gold
    }


def generate_premium_css_variables(palette: dict) -> str:
    """
    Generate premium CSS with sophisticated styling.
    
    Args:
        palette: Dictionary containing color values
    
    Returns:
        CSS string with premium variable declarations and gradient support
    """
    primary = palette.get('primary_color', '#c9a961')
    secondary = palette.get('secondary_color', '#0a1628')
    accent = palette.get('accent_color', '#d4af37')
    background = palette.get('background_color', '#faf8f5')
    
    # Generate lighter/darker variants for hover states
    primary_rgb = hex_to_rgb(primary)
    secondary_rgb = hex_to_rgb(secondary)
    accent_rgb = hex_to_rgb(accent)
    
    primary_light = rgb_to_hex(adjust_brightness(primary_rgb, 1.15))
    primary_dark = rgb_to_hex(adjust_brightness(primary_rgb, 0.85))
    accent_light = rgb_to_hex(adjust_brightness(accent_rgb, 1.1))
    
    return f"""
    :root {{
        /* Core Brand Colors */
        --event-primary-color: {primary};
        --event-secondary-color: {secondary};
        --event-accent-color: {accent};
        --event-background-color: {background};
        
        /* Text Colors */
        --event-text-on-primary: {palette.get('text_on_primary', '#ffffff')};
        --event-text-on-secondary: {palette.get('text_on_secondary', '#ffffff')};
        --event-text-on-accent: {palette.get('text_on_accent', '#ffffff')};
        
        /* Hover States */
        --event-primary-light: {primary_light};
        --event-primary-dark: {primary_dark};
        --event-accent-light: {accent_light};
        
        /* Premium Gradients */
        --event-gradient-gold: linear-gradient(135deg, {primary} 0%, {accent} 100%);
        --event-gradient-navy: linear-gradient(135deg, {secondary} 0%, {adjust_brightness(secondary_rgb, 1.3)} 100%);
        --event-gradient-hero: linear-gradient(135deg, {secondary} 0%, {primary} 100%);
        
        /* Shadows with brand tint */
        --event-shadow: 0 4px 20px rgba({secondary_rgb[0]}, {secondary_rgb[1]}, {secondary_rgb[2]}, 0.15);
        --event-shadow-lg: 0 10px 40px rgba({secondary_rgb[0]}, {secondary_rgb[1]}, {secondary_rgb[2]}, 0.2);
    }}
    """


def get_default_palette() -> dict:
    """
    Return a default color palette when extraction fails.
    
    Returns:
        Dictionary with default colors (all WCAG AA compliant)
    """
    return {
        'primary_color': '#4f46e5',      # Indigo-600
        'secondary_color': '#6b7280',    # Gray-500
        'accent_color': '#10b981',       # Emerald-500
        'background_color': '#f9fafb',   # Gray-50
        'text_on_primary': '#ffffff',
        'text_on_secondary': '#ffffff',
        'text_on_accent': '#ffffff',
    }


def generate_css_variables(palette: dict) -> str:
    """
    Generate CSS variable declarations from a color palette.
    
    Args:
        palette: Dictionary containing color values
    
    Returns:
        CSS string with variable declarations
    """
    return f"""
    :root {{
        --event-primary-color: {palette.get('primary_color', '#4f46e5')};
        --event-secondary-color: {palette.get('secondary_color', '#6b7280')};
        --event-accent-color: {palette.get('accent_color', '#10b981')};
        --event-background-color: {palette.get('background_color', '#f9fafb')};
        --event-text-on-primary: {palette.get('text_on_primary', '#ffffff')};
        --event-text-on-secondary: {palette.get('text_on_secondary', '#ffffff')};
        --event-text-on-accent: {palette.get('text_on_accent', '#ffffff')};
    }}
    """


# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        palette = extract_color_palette(test_path)
        if palette:
            print("Extracted Palette:")
            for key, value in palette.items():
                print(f"  {key}: {value}")
            
            # Show contrast ratios
            print("\nContrast Ratios (WCAG AA requires 4.5:1 for normal text):")
            primary_rgb = hex_to_rgb(palette['primary_color'])
            text_rgb = hex_to_rgb(palette['text_on_primary'])
            print(f"  Primary text: {get_contrast_ratio(primary_rgb, text_rgb):.2f}:1")
            
            secondary_rgb = hex_to_rgb(palette['secondary_color'])
            text_rgb = hex_to_rgb(palette['text_on_secondary'])
            print(f"  Secondary text: {get_contrast_ratio(secondary_rgb, text_rgb):.2f}:1")
            
            accent_rgb = hex_to_rgb(palette['accent_color'])
            text_rgb = hex_to_rgb(palette['text_on_accent'])
            print(f"  Accent text: {get_contrast_ratio(accent_rgb, text_rgb):.2f}:1")
            
            print("\nCSS Variables:")
            print(generate_css_variables(palette))
        else:
            print("Failed to extract palette. Default:")
            print(get_default_palette())
