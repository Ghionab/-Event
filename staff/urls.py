"""
Staff Portal URL Configuration
"""
from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Event list
    path('events/', views.event_list, name='event_list'),

    # Usher-only validation (no event selection)
    path('usher/validate/', views.usher_validation, name='usher_validation'),
    path('usher/validate/manual/', views.usher_manual_checkin, name='usher_manual_checkin'),
    path('usher/validate/qr/', views.usher_qr_checkin, name='usher_qr_checkin'),
    
    # Event dashboard with QR scanner
    path('events/<int:event_id>/', views.event_dashboard, name='event_dashboard'),
    
    # QR code check-in
    path('events/<int:event_id>/qr-checkin/', views.qr_checkin, name='qr_checkin'),
    
    # Manual check-in
    path('checkin/<int:registration_id>/', views.manual_checkin, name='manual_checkin'),
    
    # Real-time stats API
    path('events/<int:event_id>/stats/', views.checkin_stats, name='checkin_stats'),
]
