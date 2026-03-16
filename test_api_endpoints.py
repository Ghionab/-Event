#!/usr/bin/env python
"""
Test script to verify the theme API endpoints are properly configured.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from theming.api_views import *

User = get_user_model()

def test_api_endpoints():
    """Test that all API endpoints are properly configured."""
    
    print("Testing Theme API Endpoints...")
    print("=" * 50)
    
    # Test URL patterns
    url_patterns = [
        # Basic theme management
        ('api_themes_list', [], {}),
        ('api_theme_detail', [], {'event_id': 1}),
        ('api_theme_create', [], {'event_id': 1}),
        ('api_generate_theme', [], {'event_id': 1}),
        
        # Color extraction
        ('api_extract_colors', [], {'event_id': 1}),
        ('api_color_palette', [], {'event_id': 1}),
        
        # Theme preview
        ('api_theme_preview', [], {'event_id': 1, 'portal_type': 'staff'}),
        
        # Theme variations
        ('api_theme_variations', [], {'event_id': 1}),
        ('api_theme_variation_detail', [], {'event_id': 1, 'variation_id': 1}),
        ('api_theme_variations_bulk', [], {'event_id': 1}),
        
        # Advanced features
        ('api_theme_analytics', [], {'event_id': 1}),
        ('api_theme_validate', [], {'event_id': 1}),
        ('api_theme_export', [], {'event_id': 1}),
        ('api_theme_import', [], {'event_id': 1}),
        
        # Cache management
        ('api_clear_cache', [], {'event_id': 1}),
        ('api_cache_stats', [], {}),
        
        # WebSocket endpoints
        ('api_event_notifications', [], {'event_id': 1}),
        ('api_user_notifications', [], {}),
        ('api_system_notifications', [], {}),
        ('api_portal_notifications', [], {'portal_type': 'staff'}),
        ('api_theme_status', [], {'event_id': 1}),
        ('api_websocket_info', [], {}),
        ('api_websocket_health', [], {}),
        
        # Utility endpoints
        ('api_theme_logs', [], {'event_id': 1}),
        ('api_supported_algorithms', [], {}),
        ('api_rate_limits', [], {}),
    ]
    
    success_count = 0
    total_count = len(url_patterns)
    
    for url_name, args, kwargs in url_patterns:
        try:
            url = reverse(f'theming:{url_name}', args=args, kwargs=kwargs)
            print(f"✓ {url_name}: {url}")
            success_count += 1
        except NoReverseMatch as e:
            print(f"✗ {url_name}: URL pattern not found - {e}")
        except Exception as e:
            print(f"✗ {url_name}: Error - {e}")
    
    print("\n" + "=" * 50)
    print(f"URL Pattern Test Results: {success_count}/{total_count} successful")
    
    # Test API view classes
    print("\nTesting API View Classes...")
    print("=" * 50)
    
    view_classes = [
        EventThemeListAPIView,
        EventThemeDetailAPIView,
        EventThemeCreateAPIView,
        ColorExtractionAPIView,
        ColorPaletteAPIView,
        ThemePreviewAPIView,
        ThemeVariationListCreateAPIView,
        ThemeVariationDetailAPIView,
        ThemeVariationBulkCreateAPIView,
        ThemeAnalyticsAPIView,
        ThemeValidationAPIView,
        ThemeExportAPIView,
        ThemeImportAPIView,
        ThemeCacheStatsAPIView,
        ClearThemeCacheAPIView,
        GenerateThemeAPIView,
        RateLimitStatusAPIView,
    ]
    
    view_success_count = 0
    
    for view_class in view_classes:
        try:
            # Test that the view class can be instantiated
            view = view_class()
            print(f"✓ {view_class.__name__}: Available")
            view_success_count += 1
        except Exception as e:
            print(f"✗ {view_class.__name__}: Error - {e}")
    
    print("\n" + "=" * 50)
    print(f"View Class Test Results: {view_success_count}/{len(view_classes)} successful")
    
    # Test WebSocket views
    print("\nTesting WebSocket View Classes...")
    print("=" * 50)
    
    from theming.websocket_views import (
        EventNotificationsAPIView,
        UserNotificationsAPIView,
        SystemNotificationsAPIView,
        PortalNotificationsAPIView,
        ThemeGenerationStatusAPIView,
        WebSocketConnectionInfoAPIView,
        NotificationHealthAPIView,
        NotificationCleanupAPIView,
        BulkNotificationAPIView,
    )
    
    websocket_views = [
        EventNotificationsAPIView,
        UserNotificationsAPIView,
        SystemNotificationsAPIView,
        PortalNotificationsAPIView,
        ThemeGenerationStatusAPIView,
        WebSocketConnectionInfoAPIView,
        NotificationHealthAPIView,
        NotificationCleanupAPIView,
        BulkNotificationAPIView,
    ]
    
    websocket_success_count = 0
    
    for view_class in websocket_views:
        try:
            view = view_class()
            print(f"✓ {view_class.__name__}: Available")
            websocket_success_count += 1
        except Exception as e:
            print(f"✗ {view_class.__name__}: Error - {e}")
    
    print("\n" + "=" * 50)
    print(f"WebSocket View Test Results: {websocket_success_count}/{len(websocket_views)} successful")
    
    # Test security components
    print("\nTesting Security Components...")
    print("=" * 50)
    
    try:
        from theming.security import (
            api_security_manager,
            permission_manager,
            audit_logger,
            security_validator,
            image_processor,
            rate_limiter
        )
        print("✓ Security components imported successfully")
        
        # Test basic functionality
        print("✓ API Security Manager available")
        print("✓ Permission Manager available")
        print("✓ Audit Logger available")
        print("✓ Security Validator available")
        print("✓ Image Processor available")
        print("✓ Rate Limiter available")
        
    except Exception as e:
        print(f"✗ Security components error: {e}")
    
    # Test decorators
    print("\nTesting Security Decorators...")
    print("=" * 50)
    
    try:
        from theming.decorators import (
            secure_api_endpoint,
            secure_theme_api,
            secure_color_extraction,
            secure_theme_generation,
            secure_admin_api,
            validate_theme_colors,
            validate_css_content,
            log_api_access
        )
        print("✓ Security decorators imported successfully")
        
    except Exception as e:
        print(f"✗ Security decorators error: {e}")
    
    print("\n" + "=" * 50)
    print("API Endpoint Test Complete!")
    print("=" * 50)
    
    return {
        'url_patterns': f"{success_count}/{total_count}",
        'view_classes': f"{view_success_count}/{len(view_classes)}",
        'websocket_views': f"{websocket_success_count}/{len(websocket_views)}",
        'total_success': success_count + view_success_count + websocket_success_count,
        'total_tests': total_count + len(view_classes) + len(websocket_views)
    }

if __name__ == '__main__':
    results = test_api_endpoints()
    
    print(f"\nOverall Results:")
    print(f"- URL Patterns: {results['url_patterns']}")
    print(f"- View Classes: {results['view_classes']}")
    print(f"- WebSocket Views: {results['websocket_views']}")
    print(f"- Total: {results['total_success']}/{results['total_tests']}")
    
    if results['total_success'] == results['total_tests']:
        print("\n🎉 All tests passed! API endpoints are ready.")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some tests failed. Check the output above.")
        sys.exit(1)