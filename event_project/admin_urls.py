"""
URL patterns for admin-only security and system management functions
"""
from django.urls import path
from . import admin_views

app_name = 'admin_custom'

urlpatterns = [
    # Security Dashboard
    path('security/', admin_views.admin_security_dashboard, name='security_dashboard'),
    
    # User Management
    path('users/', admin_views.admin_user_management, name='user_management'),
    path('users/<int:user_id>/', admin_views.admin_user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-staff/', admin_views.admin_toggle_staff, name='toggle_staff'),
    path('users/<int:user_id>/toggle-superuser/', admin_views.admin_toggle_superuser, name='toggle_superuser'),
    
    # System Monitoring
    path('events/', admin_views.admin_event_overview, name='event_overview'),
    path('registrations/', admin_views.admin_registration_monitoring, name='registration_monitoring'),
    
    # Logs and Auditing
    path('logs/', admin_views.admin_system_logs, name='system_logs'),
    path('audit/', admin_views.admin_audit_events, name='audit_events'),
]
