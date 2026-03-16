from rest_framework import serializers
from django.contrib.auth import get_user_model
from events.models import Event
from .models import EventTheme, ColorPalette, ThemeVariation, ThemeCache, ThemeGenerationLog

User = get_user_model()


class ColorPaletteSerializer(serializers.ModelSerializer):
    """Serializer for color palette data"""
    
    class Meta:
        model = ColorPalette
        fields = [
            'extracted_colors', 'source_image', 'extraction_algorithm',
            'extraction_parameters', 'color_diversity_score', 'overall_confidence',
            'created_at'
        ]
        read_only_fields = ['created_at']


class ThemeVariationSerializer(serializers.ModelSerializer):
    """Serializer for theme variations"""
    
    class Meta:
        model = ThemeVariation
        fields = [
            'id', 'variation_type', 'css_content', 'css_hash',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'css_hash', 'created_at']


class ThemeGenerationLogSerializer(serializers.ModelSerializer):
    """Serializer for theme generation logs"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ThemeGenerationLog
        fields = [
            'id', 'operation_type', 'status', 'processing_time_ms',
            'error_message', 'extraction_confidence', 'source_image_path',
            'user_name', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'user_name', 'created_at']


class EventThemeSerializer(serializers.ModelSerializer):
    """Serializer for event themes"""
    palette = ColorPaletteSerializer(read_only=True)
    variations = ThemeVariationSerializer(many=True, read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    
    class Meta:
        model = EventTheme
        fields = [
            'id', 'event_title', 'primary_color', 'secondary_color',
            'accent_color', 'neutral_light', 'neutral_dark', 'css_content',
            'css_hash', 'extraction_confidence', 'is_fallback',
            'generation_method', 'wcag_compliant', 'contrast_adjustments_made',
            'cache_key', 'last_accessed', 'access_count', 'created_at',
            'updated_at', 'palette', 'variations'
        ]
        read_only_fields = [
            'id', 'event_title', 'css_hash', 'cache_key', 'last_accessed',
            'access_count', 'created_at', 'updated_at', 'palette', 'variations'
        ]


class EventThemeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating event themes"""
    
    class Meta:
        model = EventTheme
        fields = [
            'primary_color', 'secondary_color', 'accent_color',
            'neutral_light', 'neutral_dark', 'generation_method'
        ]
    
    def validate_primary_color(self, value):
        """Validate hex color format"""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be in hex format (#RRGGBB)")
        try:
            int(value[1:], 16)
        except ValueError:
            raise serializers.ValidationError("Invalid hex color format")
        return value
    
    def validate_secondary_color(self, value):
        return self.validate_primary_color(value)
    
    def validate_accent_color(self, value):
        return self.validate_primary_color(value)
    
    def validate_neutral_light(self, value):
        return self.validate_primary_color(value)
    
    def validate_neutral_dark(self, value):
        return self.validate_primary_color(value)


class EventThemeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating event themes"""
    
    class Meta:
        model = EventTheme
        fields = [
            'primary_color', 'secondary_color', 'accent_color',
            'neutral_light', 'neutral_dark', 'generation_method'
        ]
    
    def validate_primary_color(self, value):
        """Validate hex color format"""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be in hex format (#RRGGBB)")
        try:
            int(value[1:], 16)
        except ValueError:
            raise serializers.ValidationError("Invalid hex color format")
        return value
    
    def validate_secondary_color(self, value):
        return self.validate_primary_color(value)
    
    def validate_accent_color(self, value):
        return self.validate_primary_color(value)
    
    def validate_neutral_light(self, value):
        return self.validate_primary_color(value)
    
    def validate_neutral_dark(self, value):
        return self.validate_primary_color(value)


class ColorExtractionRequestSerializer(serializers.Serializer):
    """Serializer for color extraction requests"""
    image = serializers.ImageField(required=True)
    algorithm = serializers.ChoiceField(
        choices=['kmeans', 'colorthief', 'dominant'],
        default='kmeans',
        required=False
    )
    num_colors = serializers.IntegerField(min_value=3, max_value=10, default=5, required=False)
    
    def validate_image(self, value):
        """Validate uploaded image"""
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large (max 10MB)")
        
        # Check file format
        allowed_formats = ['PNG', 'JPEG', 'JPG', 'WebP']
        if hasattr(value, 'image') and value.image.format not in allowed_formats:
            raise serializers.ValidationError(
                f"Unsupported image format. Allowed formats: {', '.join(allowed_formats)}"
            )
        
        return value


class ColorExtractionResponseSerializer(serializers.Serializer):
    """Serializer for color extraction responses"""
    extracted_colors = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    overall_confidence = serializers.FloatField(read_only=True)
    color_diversity_score = serializers.FloatField(read_only=True)
    processing_time_ms = serializers.IntegerField(read_only=True)
    algorithm_used = serializers.CharField(read_only=True)
    image_properties = serializers.DictField(read_only=True)


class ThemePreviewSerializer(serializers.Serializer):
    """Serializer for theme preview responses"""
    portal_type = serializers.ChoiceField(
        choices=['staff', 'participant', 'organizer'],
        required=True
    )
    css_content = serializers.CharField(read_only=True)
    preview_url = serializers.URLField(read_only=True, required=False)
    compatibility_score = serializers.FloatField(read_only=True)


class ThemeVariationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating theme variations"""
    
    class Meta:
        model = ThemeVariation
        fields = ['variation_type']
    
    def validate_variation_type(self, value):
        """Ensure variation type is valid"""
        valid_types = [choice[0] for choice in ThemeVariation.VARIATION_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid variation type. Choose from: {valid_types}")
        return value


class ThemeCacheStatsSerializer(serializers.Serializer):
    """Serializer for cache statistics"""
    total_entries = serializers.IntegerField(read_only=True)
    expired_entries = serializers.IntegerField(read_only=True)
    total_access_count = serializers.IntegerField(read_only=True)
    portal_breakdown = serializers.DictField(read_only=True)
    hit_rate = serializers.FloatField(read_only=True)
    average_access_time_ms = serializers.FloatField(read_only=True)


class WebSocketEventSerializer(serializers.Serializer):
    """Serializer for WebSocket event messages"""
    event = serializers.CharField(max_length=100)
    data = serializers.DictField()
    timestamp = serializers.DateTimeField(read_only=True)
    event_id = serializers.IntegerField()
    user_id = serializers.IntegerField(required=False)


class ThemeGenerationStatusSerializer(serializers.Serializer):
    """Serializer for theme generation status updates"""
    event_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=['pending', 'processing', 'completed', 'failed']
    )
    progress_percentage = serializers.IntegerField(min_value=0, max_value=100, required=False)
    estimated_completion = serializers.DateTimeField(required=False)
    error_message = serializers.CharField(required=False)
    theme_id = serializers.IntegerField(required=False)
    preview_url = serializers.URLField(required=False)