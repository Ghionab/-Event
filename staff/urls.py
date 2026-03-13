"""
Staff Portal URL Configuration
"""
from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Event list
    path('events/', views.event_list, name='event_list'),
    
    # Event dashboard with QR scanner
    path('events/<int:event_id>/', views.event_dashboard, name='event_dashboard'),
    
    # QR code check-in
    path('events/<int:event_id>/qr-checkin/', views.qr_checkin, name='qr_checkin'),
    
    # Manual check-in
    path('checkin/<int:registration_id>/', views.manual_checkin, name='manual_checkin'),
    
    # Real-time stats API
    path('events/<int:event_id>/stats/', views.checkin_stats, name='checkin_stats'),
]
