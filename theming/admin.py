from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import EventTheme, ColorPalette, ThemeVariation, ThemeCache, ThemeGenerationLog


@admin.register(EventTheme)
class EventThemeAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'generation_method', 'extraction_confidence', 
        'wcag_compliant', 'is_fallback', 'access_count', 'last_accessed'
    ]
    list_filter = [
        'generation_method', 'wcag_compliant', 'is_fallback', 
        'contrast_adjustments_made', 'created_at'
    ]
    search_fields = ['event__title', 'cache_key', 'css_hash']
    readonly_fields = [
        'css_hash', 'cache_key', 'access_count', 'last_accessed', 
        'created_at', 'updated_at', 'color_preview'
    ]
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event',)
        }),
        ('Color Palette', {
            'fields': ('primary_color', 'secondary_color', 'accent_color', 
                      'neutral_light', 'neutral_dark', 'color_preview'),
            'classes': ('wide',)
        }),
        ('Generation Details', {
            'fields': ('generation_method', 'extraction_confidence', 'is_fallback'),
        }),
        ('Accessibility', {
            'fields': ('wcag_compliant', 'contrast_adjustments_made'),
        }),
        ('CSS Content', {
            'fields': ('css_content', 'css_hash'),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('cache_key', 'access_count', 'last_accessed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def color_preview(self, obj):
        """Display color swatches for the theme"""
        if not obj.primary_color:
            return "No colors set"
        
        colors = [
            ('Primary', obj.primary_color),
            ('Secondary', obj.secondary_color),
            ('Accent', obj.accent_color),
            ('Light', obj.neutral_light),
            ('Dark', obj.neutral_dark),
        ]
        
        swatches = []
        for name, color in colors:
            if color:
                swatches.append(
                    f'<div style="display: inline-block; margin-right: 10px;">'
                    f'<div style="width: 30px; height: 30px; background-color: {color}; '
                    f'border: 1px solid #ccc; display: inline-block; vertical-align: middle;"></div>'
                    f'<span style="margin-left: 5px; vertical-align: middle;">{name}: {color}</span>'
                    f'</div>'
                )
        
        return mark_safe('<div>' + ''.join(swatches) + '</div>')
    
    color_preview.short_description = "Color Preview"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event')


class ColorPaletteInline(admin.StackedInline):
    model = ColorPalette
    extra = 0
    readonly_fields = ['created_at', 'extracted_colors_display']
    
    def extracted_colors_display(self, obj):
        """Display extracted colors in a readable format"""
        if not obj.extracted_colors:
            return "No colors extracted"
        
        colors_html = []
        for color_data in obj.extracted_colors[:10]:  # Show first 10 colors
            color = color_data.get('color', '#000000')
            confidence = color_data.get('confidence', 0)
            frequency = color_data.get('frequency', 0)
            
            colors_html.append(
                f'<div style="display: inline-block; margin: 5px; text-align: center;">'
                f'<div style="width: 40px; height: 40px; background-color: {color}; '
                f'border: 1px solid #ccc; margin-bottom: 2px;"></div>'
                f'<div style="font-size: 10px;">{color}</div>'
                f'<div style="font-size: 9px;">C: {confidence:.2f}</div>'
                f'<div style="font-size: 9px;">F: {frequency:.2f}</div>'
                f'</div>'
            )
        
        return mark_safe('<div>' + ''.join(colors_html) + '</div>')
    
    extracted_colors_display.short_description = "Extracted Colors"


@admin.register(ColorPalette)
class ColorPaletteAdmin(admin.ModelAdmin):
    list_display = [
        'theme', 'extraction_algorithm', 'overall_confidence', 
        'color_diversity_score', 'created_at'
    ]
    list_filter = ['extraction_algorithm', 'created_at']
    search_fields = ['theme__event__title', 'source_image']
    readonly_fields = ['created_at', 'extracted_colors_display']
    
    def extracted_colors_display(self, obj):
        """Display extracted colors in a readable format"""
        if not obj.extracted_colors:
            return "No colors extracted"
        
        colors_html = []
        for color_data in obj.extracted_colors:
            color = color_data.get('color', '#000000')
            confidence = color_data.get('confidence', 0)
            frequency = color_data.get('frequency', 0)
            name = color_data.get('name', 'Unnamed')
            
            colors_html.append(
                f'<div style="display: inline-block; margin: 5px; text-align: center; width: 80px;">'
                f'<div style="width: 60px; height: 60px; background-color: {color}; '
                f'border: 1px solid #ccc; margin-bottom: 2px;"></div>'
                f'<div style="font-size: 11px; font-weight: bold;">{name}</div>'
                f'<div style="font-size: 10px;">{color}</div>'
                f'<div style="font-size: 9px;">Confidence: {confidence:.2f}</div>'
                f'<div style="font-size: 9px;">Frequency: {frequency:.2f}</div>'
                f'</div>'
            )
        
        return mark_safe('<div style="max-width: 800px;">' + ''.join(colors_html) + '</div>')
    
    extracted_colors_display.short_description = "Extracted Colors"


class ThemeVariationInline(admin.TabularInline):
    model = ThemeVariation
    extra = 0
    readonly_fields = ['css_hash', 'created_at']


@admin.register(ThemeVariation)
class ThemeVariationAdmin(admin.ModelAdmin):
    list_display = ['base_theme', 'variation_type', 'is_active', 'created_at']
    list_filter = ['variation_type', 'is_active', 'created_at']
    search_fields = ['base_theme__event__title']
    readonly_fields = ['css_hash', 'created_at']


@admin.register(ThemeCache)
class ThemeCacheAdmin(admin.ModelAdmin):
    list_display = [
        'cache_key', 'theme', 'portal_type', 'access_count', 
        'last_accessed', 'expires_at', 'is_expired_display'
    ]
    list_filter = ['portal_type', 'created_at', 'expires_at']
    search_fields = ['cache_key', 'theme__event__title']
    readonly_fields = ['created_at', 'last_accessed', 'is_expired_display']
    
    def is_expired_display(self, obj):
        """Display whether cache entry is expired"""
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        else:
            return format_html('<span style="color: green;">Valid</span>')
    
    is_expired_display.short_description = "Status"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('theme__event')


@admin.register(ThemeGenerationLog)
class ThemeGenerationLogAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'operation_type', 'status', 'processing_time_ms', 
        'extraction_confidence', 'user', 'created_at'
    ]
    list_filter = [
        'operation_type', 'status', 'created_at'
    ]
    search_fields = ['event__title', 'error_message', 'source_image_path']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('event', 'operation_type', 'status', 'user')
        }),
        ('Performance', {
            'fields': ('processing_time_ms', 'extraction_confidence')
        }),
        ('Source Information', {
            'fields': ('source_image_path',)
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event', 'user')


# Add inlines to EventThemeAdmin
EventThemeAdmin.inlines = [ColorPaletteInline, ThemeVariationInline]


# Custom admin site configuration
admin.site.site_header = "Event Management System"
admin.site.site_title = "Event Management"
admin.site.index_title = "Welcome to Event Management Administration"