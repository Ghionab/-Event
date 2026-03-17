from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from events.models import Event
from .models import EventTheme, ColorPalette, ThemeVariation, ThemeCache, ThemeGenerationLog
import json

User = get_user_model()


class EventThemeModelTest(TestCase):
    """Test EventTheme model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
    
    def test_event_theme_creation(self):
        """Test creating an EventTheme"""
        theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
            generation_method='auto',
            extraction_confidence=0.85
        )
        
        self.assertEqual(theme.event, self.event)
        self.assertEqual(theme.primary_color, '#007bff')
        self.assertEqual(theme.generation_method, 'auto')
        self.assertEqual(theme.extraction_confidence, 0.85)
        self.assertTrue(theme.wcag_compliant)
        self.assertFalse(theme.is_fallback)
        self.assertIsNotNone(theme.css_hash)
        self.assertIsNotNone(theme.cache_key)
    
    def test_theme_string_representation(self):
        """Test EventTheme __str__ method"""
        theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
        )
        
        self.assertEqual(str(theme), f'Theme for {self.event.title}')
    
    def test_increment_access_count(self):
        """Test incrementing access count"""
        theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
        )
        
        initial_count = theme.access_count
        theme.increment_access_count()
        
        self.assertEqual(theme.access_count, initial_count + 1)


class ColorPaletteModelTest(TestCase):
    """Test ColorPalette model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
        self.theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
        )
    
    def test_color_palette_creation(self):
        """Test creating a ColorPalette"""
        extracted_colors = [
            {"color": "#007bff", "confidence": 0.95, "frequency": 0.35, "name": "Blue"},
            {"color": "#28a745", "confidence": 0.88, "frequency": 0.28, "name": "Green"},
            {"color": "#6c757d", "confidence": 0.75, "frequency": 0.15, "name": "Gray"},
        ]
        
        palette = ColorPalette.objects.create(
            theme=self.theme,
            extracted_colors=extracted_colors,
            source_image='test_logo.png',
            extraction_algorithm='kmeans',
            color_diversity_score=0.85,
            overall_confidence=0.82
        )
        
        self.assertEqual(palette.theme, self.theme)
        self.assertEqual(len(palette.extracted_colors), 3)
        self.assertEqual(palette.extraction_algorithm, 'kmeans')
        self.assertEqual(palette.color_diversity_score, 0.85)
        self.assertEqual(palette.overall_confidence, 0.82)
    
    def test_get_primary_colors(self):
        """Test getting primary colors by confidence"""
        extracted_colors = [
            {"color": "#007bff", "confidence": 0.95, "frequency": 0.35, "name": "Blue"},
            {"color": "#28a745", "confidence": 0.88, "frequency": 0.28, "name": "Green"},
            {"color": "#6c757d", "confidence": 0.75, "frequency": 0.15, "name": "Gray"},
        ]
        
        palette = ColorPalette.objects.create(
            theme=self.theme,
            extracted_colors=extracted_colors,
            source_image='test_logo.png'
        )
        
        primary_colors = palette.get_primary_colors(2)
        self.assertEqual(len(primary_colors), 2)
        self.assertEqual(primary_colors[0]['color'], '#007bff')  # Highest confidence
        self.assertEqual(primary_colors[1]['color'], '#28a745')  # Second highest
    
    def test_get_color_by_frequency(self):
        """Test getting colors by frequency"""
        extracted_colors = [
            {"color": "#007bff", "confidence": 0.95, "frequency": 0.35, "name": "Blue"},
            {"color": "#28a745", "confidence": 0.88, "frequency": 0.45, "name": "Green"},  # Highest frequency
            {"color": "#6c757d", "confidence": 0.75, "frequency": 0.20, "name": "Gray"},
        ]
        
        palette = ColorPalette.objects.create(
            theme=self.theme,
            extracted_colors=extracted_colors,
            source_image='test_logo.png'
        )
        
        frequent_colors = palette.get_color_by_frequency(2)
        self.assertEqual(len(frequent_colors), 2)
        self.assertEqual(frequent_colors[0]['color'], '#28a745')  # Highest frequency
        self.assertEqual(frequent_colors[1]['color'], '#007bff')  # Second highest


class ThemeVariationModelTest(TestCase):
    """Test ThemeVariation model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
        self.theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
        )
    
    def test_theme_variation_creation(self):
        """Test creating a ThemeVariation"""
        variation = ThemeVariation.objects.create(
            base_theme=self.theme,
            variation_type='dark',
            css_content='/* dark theme css */',
        )
        
        self.assertEqual(variation.base_theme, self.theme)
        self.assertEqual(variation.variation_type, 'dark')
        self.assertTrue(variation.is_active)
        self.assertIsNotNone(variation.css_hash)
    
    def test_unique_variation_constraint(self):
        """Test that variation types are unique per theme"""
        ThemeVariation.objects.create(
            base_theme=self.theme,
            variation_type='dark',
            css_content='/* dark theme css */',
        )
        
        # Attempting to create another 'dark' variation should raise an error
        with self.assertRaises(Exception):
            ThemeVariation.objects.create(
                base_theme=self.theme,
                variation_type='dark',
                css_content='/* another dark theme css */',
            )


class ThemeCacheModelTest(TestCase):
    """Test ThemeCache model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
        self.theme = EventTheme.objects.create(
            event=self.event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#f8f9fa',
            neutral_dark='#343a40',
            css_content='/* test css */',
        )
    
    def test_theme_cache_creation(self):
        """Test creating a ThemeCache entry"""
        cache_entry = ThemeCache.objects.create(
            cache_key='test_cache_key',
            theme=self.theme,
            css_content='/* cached css */',
            portal_type='participant',
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        
        self.assertEqual(cache_entry.cache_key, 'test_cache_key')
        self.assertEqual(cache_entry.theme, self.theme)
        self.assertEqual(cache_entry.portal_type, 'participant')
        self.assertFalse(cache_entry.is_expired())
    
    def test_cache_expiration(self):
        """Test cache expiration functionality"""
        # Create expired cache entry
        cache_entry = ThemeCache.objects.create(
            cache_key='expired_cache_key',
            theme=self.theme,
            css_content='/* cached css */',
            portal_type='participant',
            expires_at=timezone.now() - timezone.timedelta(hours=1)  # Expired 1 hour ago
        )
        
        self.assertTrue(cache_entry.is_expired())
    
    def test_increment_access_count(self):
        """Test incrementing cache access count"""
        cache_entry = ThemeCache.objects.create(
            cache_key='test_cache_key',
            theme=self.theme,
            css_content='/* cached css */',
            portal_type='participant',
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        
        initial_count = cache_entry.access_count
        cache_entry.increment_access_count()
        
        self.assertEqual(cache_entry.access_count, initial_count + 1)


class ThemeGenerationLogModelTest(TestCase):
    """Test ThemeGenerationLog model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
    
    def test_log_creation(self):
        """Test creating a ThemeGenerationLog entry"""
        log_entry = ThemeGenerationLog.objects.create(
            event=self.event,
            operation_type='generation',
            status='success',
            processing_time_ms=150,
            extraction_confidence=0.85,
            user=self.user
        )
        
        self.assertEqual(log_entry.event, self.event)
        self.assertEqual(log_entry.operation_type, 'generation')
        self.assertEqual(log_entry.status, 'success')
        self.assertEqual(log_entry.processing_time_ms, 150)
        self.assertEqual(log_entry.extraction_confidence, 0.85)
        self.assertEqual(log_entry.user, self.user)
    
    def test_log_operation_convenience_method(self):
        """Test the log_operation convenience method"""
        log_entry = ThemeGenerationLog.log_operation(
            event=self.event,
            operation_type='fallback',
            status='warning',
            user=self.user,
            error_message='Color extraction failed'
        )
        
        self.assertEqual(log_entry.event, self.event)
        self.assertEqual(log_entry.operation_type, 'fallback')
        self.assertEqual(log_entry.status, 'warning')
        self.assertEqual(log_entry.error_message, 'Color extraction failed')


class ThemingViewsTest(TestCase):
    """Test theming views functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=self.user
        )
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_theme_list_view(self):
        """Test theme list view"""
        response = self.client.get(reverse('theming:theme_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Event Themes')
    
    def test_event_theme_detail_view(self):
        """Test event theme detail view"""
        response = self.client.get(reverse('theming:event_theme', kwargs={'event_id': self.event.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)
        
        # Check that a theme was created
        self.assertTrue(EventTheme.objects.filter(event=self.event).exists())
    
    def test_generate_theme_view(self):
        """Test theme generation view"""
        response = self.client.post(reverse('theming:generate_theme', kwargs={'event_id': self.event.id}))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('Theme generated successfully', data['message'])
        
        # Check that a theme was created
        theme = EventTheme.objects.get(event=self.event)
        self.assertEqual(theme.generation_method, 'auto')
    
    def test_extract_colors_view(self):
        """Test color extraction view"""
        response = self.client.post(reverse('theming:extract_colors', kwargs={'event_id': self.event.id}))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('extracted_colors', data)
        self.assertGreater(len(data['extracted_colors']), 0)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access themes"""
        # Create another user and event
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='User'
        )
        other_event = Event.objects.create(
            title='Other Event',
            description='Other Description',
            start_date=timezone.now() + timezone.timedelta(days=30),
            end_date=timezone.now() + timezone.timedelta(days=31),
            organizer=other_user
        )
        
        # Try to access other user's event theme
        response = self.client.get(reverse('theming:event_theme', kwargs={'event_id': other_event.id}))
        self.assertEqual(response.status_code, 404)  # Should not be found for this user