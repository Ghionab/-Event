from django.urls import path, include
from . import views, api_views, websocket_views

app_name = 'theming'

urlpatterns = [
    # Theme management URLs (Web interface)
    path('', views.ThemeListView.as_view(), name='theme_list'),
    path('event/<int:event_id>/', views.EventThemeDetailView.as_view(), name='event_theme'),
    path('event/<int:event_id>/generate/', views.GenerateThemeView.as_view(), name='generate_theme'),
    path('event/<int:event_id>/preview/<str:portal_type>/', views.ThemePreviewView.as_view(), name='theme_preview'),
    
    # Color extraction URLs (Web interface)
    path('event/<int:event_id>/extract-colors/', views.ExtractColorsView.as_view(), name='extract_colors'),
    path('event/<int:event_id>/color-palette/', views.ColorPaletteView.as_view(), name='color_palette'),
    
    # Theme variations (Web interface)
    path('event/<int:event_id>/variations/', views.ThemeVariationListView.as_view(), name='theme_variations'),
    path('event/<int:event_id>/variations/create/', views.CreateThemeVariationView.as_view(), name='create_variation'),
    
    # Cache management (Web interface)
    path('event/<int:event_id>/cache/clear/', views.ClearThemeCacheView.as_view(), name='clear_cache'),
    path('cache/stats/', views.CacheStatsView.as_view(), name='cache_stats'),
    
    # RESTful API endpoints
    path('api/v1/', include([
        # Theme management API
        path('themes/', api_views.EventThemeListAPIView.as_view(), name='api_themes_list'),
        path('events/<int:event_id>/theme/', api_views.EventThemeDetailAPIView.as_view(), name='api_theme_detail'),
        path('events/<int:event_id>/theme/create/', api_views.EventThemeCreateAPIView.as_view(), name='api_theme_create'),
        path('events/<int:event_id>/theme/generate/', api_views.GenerateThemeAPIView.as_view(), name='api_generate_theme'),
        
        # Color extraction API
        path('events/<int:event_id>/extract-colors/', api_views.ColorExtractionAPIView.as_view(), name='api_extract_colors'),
        path('events/<int:event_id>/color-palette/', api_views.ColorPaletteAPIView.as_view(), name='api_color_palette'),
        
        # Theme preview API
        path('events/<int:event_id>/theme/preview/<str:portal_type>/', api_views.ThemePreviewAPIView.as_view(), name='api_theme_preview'),
        
        # Theme variations API
        path('events/<int:event_id>/theme/variations/', api_views.ThemeVariationListCreateAPIView.as_view(), name='api_theme_variations'),
        path('events/<int:event_id>/theme/variations/<int:variation_id>/', api_views.ThemeVariationDetailAPIView.as_view(), name='api_theme_variation_detail'),
        
        # Cache management API
        path('events/<int:event_id>/theme/cache/', api_views.ClearThemeCacheAPIView.as_view(), name='api_clear_cache'),
        path('themes/cache/stats/', api_views.ThemeCacheStatsAPIView.as_view(), name='api_cache_stats'),
        
        # Utility API endpoints
        path('events/<int:event_id>/theme/logs/', api_views.theme_generation_logs, name='api_theme_logs'),
        path('themes/algorithms/', api_views.supported_algorithms, name='api_supported_algorithms'),
        
        # Advanced theme management API
        path('events/<int:event_id>/theme/variations/bulk/', api_views.ThemeVariationBulkCreateAPIView.as_view(), name='api_theme_variations_bulk'),
        path('events/<int:event_id>/theme/analytics/', api_views.ThemeAnalyticsAPIView.as_view(), name='api_theme_analytics'),
        path('events/<int:event_id>/theme/validate/', api_views.ThemeValidationAPIView.as_view(), name='api_theme_validate'),
        path('events/<int:event_id>/theme/export/', api_views.ThemeExportAPIView.as_view(), name='api_theme_export'),
        path('events/<int:event_id>/theme/import/', api_views.ThemeImportAPIView.as_view(), name='api_theme_import'),
        path('user/rate-limits/', api_views.RateLimitStatusAPIView.as_view(), name='api_rate_limits'),
        
        # WebSocket and real-time notification API
        path('notifications/events/<int:event_id>/', websocket_views.EventNotificationsAPIView.as_view(), name='api_event_notifications'),
        path('notifications/user/', websocket_views.UserNotificationsAPIView.as_view(), name='api_user_notifications'),
        path('notifications/system/', websocket_views.SystemNotificationsAPIView.as_view(), name='api_system_notifications'),
        path('notifications/portal/<str:portal_type>/', websocket_views.PortalNotificationsAPIView.as_view(), name='api_portal_notifications'),
        path('notifications/health/', websocket_views.NotificationHealthAPIView.as_view(), name='api_notification_health'),
        path('notifications/cleanup/', websocket_views.NotificationCleanupAPIView.as_view(), name='api_notification_cleanup'),
        path('notifications/bulk/', websocket_views.BulkNotificationAPIView.as_view(), name='api_bulk_notifications'),
        path('events/<int:event_id>/theme/status/', websocket_views.ThemeGenerationStatusAPIView.as_view(), name='api_theme_status'),
        path('websocket/info/', websocket_views.WebSocketConnectionInfoAPIView.as_view(), name='api_websocket_info'),
        path('websocket/health/', websocket_views.websocket_health_check, name='api_websocket_health'),
        
        # Development/testing endpoints
        path('websocket/simulate/', websocket_views.simulate_websocket_event, name='api_simulate_websocket'),
        path('websocket/test/', websocket_views.trigger_test_notifications, name='api_test_notifications'),
    ])),
    
    # Legacy API endpoints (for backward compatibility)
    path('api/', include([
        path('themes/', views.ThemeAPIView.as_view(), name='legacy_api_themes'),
        path('themes/<int:event_id>/', views.ThemeDetailAPIView.as_view(), name='legacy_api_theme_detail'),
        path('extract-colors/', views.ExtractColorsAPIView.as_view(), name='legacy_api_extract_colors'),
    ])),
]