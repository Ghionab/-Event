"""
Template tags for dynamic theme application.
"""

from django import template
from django.utils.safestring import mark_safe
from django.core.cache import cache
from ..services.portal_renderer import PortalRenderer
from ..models import EventTheme

register = template.Library()


@register.simple_tag
def theme_css(event_id, portal_type='participant'):
    """
    Generate theme CSS for specific event and portal.
    
    Usage: {% theme_css event.id 'staff' %}
    """
    try:
        renderer = PortalRenderer()
        theme = renderer.get_theme_for_event(event_id)
        
        if theme:
            css = renderer.generate_portal_css(theme, portal_type)
            return mark_safe(f'<style type="text/css">{css}</style>')
        else:
            # Return default CSS
            default_css = renderer._get_default_css(portal_type)
            return mark_safe(f'<style type="text/css">{default_css}</style>')
    
    except Exception:
        return ''


@register.simple_tag
def theme_color(event_id, color_type='primary'):
    """
    Get specific theme color.
    
    Usage: {% theme_color event.id 'primary' %}
    """
    try:
        renderer = PortalRenderer()
        theme = renderer.get_theme_for_event(event_id)
        
        if theme:
            color_map = {
                'primary': theme.primary_color,
                'secondary': theme.secondary_color,
                'accent': theme.accent_color,
                'neutral_light': theme.neutral_light,
                'neutral_dark': theme.neutral_dark,
            }
            return color_map.get(color_type, '#007bff')
        else:
            # Default colors
            default_colors = {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'accent': '#28a745',
                'neutral_light': '#f8f9fa',
                'neutral_dark': '#343a40',
            }
            return default_colors.get(color_type, '#007bff')
    
    except Exception:
        return '#007bff'


@register.inclusion_tag('theming/theme_variables.html')
def theme_variables(event_id):
    """
    Include CSS custom properties for theme.
    
    Usage: {% theme_variables event.id %}
    """
    try:
        renderer = PortalRenderer()
        theme = renderer.get_theme_for_event(event_id)
        
        if theme:
            return {
                'theme': theme,
                'colors': {
                    'primary': theme.primary_color,
                    'secondary': theme.secondary_color,
                    'accent': theme.accent_color,
                    'neutral_light': theme.neutral_light,
                    'neutral_dark': theme.neutral_dark,
                }
            }
        else:
            return {
                'theme': None,
                'colors': {
                    'primary': '#007bff',
                    'secondary': '#6c757d',
                    'accent': '#28a745',
                    'neutral_light': '#f8f9fa',
                    'neutral_dark': '#343a40',
                }
            }
    
    except Exception:
        return {'theme': None, 'colors': {}}


@register.filter
def theme_style(value, style_type):
    """
    Apply theme styling to HTML elements.
    
    Usage: {{ "Button Text"|theme_style:"primary-button" }}
    """
    try:
        style_classes = {
            'primary-button': 'btn btn-primary',
            'secondary-button': 'btn btn-secondary',
            'accent-button': 'btn btn-accent',
            'primary-card': 'card card-primary',
            'primary-text': 'text-primary',
            'secondary-text': 'text-secondary',
            'accent-text': 'text-accent',
            'primary-bg': 'bg-primary',
            'secondary-bg': 'bg-secondary',
            'accent-bg': 'bg-accent',
        }
        
        css_class = style_classes.get(style_type, '')
        if css_class:
            return mark_safe(f'<span class="{css_class}">{value}</span>')
        else:
            return value
    
    except Exception:
        return value


@register.simple_tag
def theme_compatible_check(event_id, portal_type):
    """
    Check if theme is compatible with portal.
    
    Usage: {% theme_compatible_check event.id 'staff' as is_compatible %}
    """
    try:
        renderer = PortalRenderer()
        theme = renderer.get_theme_for_event(event_id)
        
        if theme:
            return renderer.validate_portal_compatibility(theme, portal_type)
        else:
            return True  # Default theme is always compatible
    
    except Exception:
        return False


@register.simple_tag(takes_context=True)
def current_theme(context):
    """
    Get current theme from context.
    
    Usage: {% current_theme as theme %}
    """
    return context.get('theme', None)


@register.simple_tag(takes_context=True)
def current_theme_colors(context):
    """
    Get current theme colors from context.
    
    Usage: {% current_theme_colors as colors %}
    """
    return context.get('theme_colors', {})


@register.simple_tag
def theme_cache_key(event_id, portal_type):
    """
    Generate cache key for theme.
    
    Usage: {% theme_cache_key event.id 'staff' %}
    """
    return f"theme_{event_id}_{portal_type}"


@register.simple_tag
def clear_theme_cache(event_id, portal_type=None):
    """
    Clear theme cache.
    
    Usage: {% clear_theme_cache event.id 'staff' %}
    """
    try:
        renderer = PortalRenderer()
        theme = renderer.get_theme_for_event(event_id)
        
        if theme:
            renderer.clear_theme_cache(theme, portal_type)
            return "Cache cleared"
        else:
            return "No theme found"
    
    except Exception as e:
        return f"Error: {str(e)}"


@register.inclusion_tag('theming/portal_specific_styles.html')
def portal_styles(portal_type, event_id=None):
    """
    Include portal-specific styles.
    
    Usage: {% portal_styles 'staff' event.id %}
    """
    try:
        if event_id:
            renderer = PortalRenderer()
            theme = renderer.get_theme_for_event(event_id)
            
            if theme:
                css = renderer.generate_portal_css(theme, portal_type)
                return {
                    'portal_type': portal_type,
                    'css_content': css,
                    'has_theme': True
                }
        
        # Default styles
        renderer = PortalRenderer()
        default_css = renderer._get_default_css(portal_type)
        return {
            'portal_type': portal_type,
            'css_content': default_css,
            'has_theme': False
        }
    
    except Exception:
        return {
            'portal_type': portal_type,
            'css_content': '',
            'has_theme': False
        }


@register.filter
def hex_to_rgb(hex_color):
    """
    Convert hex color to RGB.
    
    Usage: {{ "#ff0000"|hex_to_rgb }}
    """
    try:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
    except Exception:
        return "rgb(0, 0, 0)"


@register.filter
def hex_to_rgba(hex_color, alpha=1.0):
    """
    Convert hex color to RGBA.
    
    Usage: {{ "#ff0000"|hex_to_rgba:0.5 }}
    """
    try:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
    except Exception:
        return f"rgba(0, 0, 0, {alpha})"


@register.simple_tag
def theme_metadata(event_id):
    """
    Get theme metadata.
    
    Usage: {% theme_metadata event.id as metadata %}
    """
    try:
        renderer = PortalRenderer()
        theme = renderer.get_theme_for_event(event_id)
        
        if theme:
            return {
                'generation_method': theme.generation_method,
                'wcag_compliant': theme.wcag_compliant,
                'is_fallback': theme.is_fallback,
                'extraction_confidence': theme.extraction_confidence,
                'last_updated': theme.updated_at,
                'access_count': theme.access_count,
            }
        else:
            return {}
    
    except Exception:
        return {}