from django.urls import path
from . import views
from . import views_auth

urlpatterns = [
    path('', views_auth.organizer_login, name='organizer_login'),
    path('login/', views_auth.organizer_login, name='organizer_login'),
    path('logout/', views_auth.organizer_logout, name='logout'),
    path('create/', views.organizer_create, name='organizer_create'),
    path('dashboard/', views.dashboard, name='organizer_dashboard'),
    path('events/', views.event_list, name='organizer_event_list'),
    path('events/create/', views.event_create, name='organizer_event_create'),
    path('events/<int:event_id>/setup/', views.event_setup, name='organizer_event_setup'),
    path('events/<int:event_id>/', views.event_detail, name='organizer_event_detail'),
    path('events/<int:event_id>/edit/', views.event_edit, name='organizer_event_edit'),
    path('events/<int:event_id>/delete/', views.event_delete, name='organizer_event_delete'),
    path('analytics/', views.analytics, name='organizer_analytics'),
    path('analytics/<int:event_id>/', views.analytics, name='organizer_analytics_event'),
    path('team/', views.team_members, name='organizer_team'),
    path('templates/', views.templates, name='organizer_templates'),
    path('templates/create/', views.template_create, name='organizer_template_create'),
    path('templates/<int:template_id>/', views.template_detail, name='organizer_template_detail'),
    path('settings/', views.settings, name='organizer_settings'),
    path('notifications/', views.notifications, name='organizer_notifications'),
    path('payouts/', views.payouts, name='organizer_payouts'),
    path('tickets/', views.ticket_management, name='organizer_ticket_management'),
]