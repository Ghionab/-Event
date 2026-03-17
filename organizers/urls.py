from django.urls import path
from . import views
from . import views_auth

app_name = 'organizers'

urlpatterns = [
    path('', views_auth.organizer_login, name='organizer_login'),
    path('login/', views_auth.organizer_login, name='organizer_login'),
    path('logout/', views_auth.organizer_logout, name='organizer_logout'),
    path('logout/', views_auth.organizer_logout, name='logout'),
    path('create/', views.organizer_create, name='organizer_create'),
    path('dashboard/', views.dashboard, name='organizer_dashboard'),
    
    # Event URLs
    path('events/', views.event_list, name='organizer_event_list'),
    path('events/create/', views.event_create, name='organizer_event_create'),
    path('events/<int:event_id>/setup/', views.event_setup, name='organizer_event_setup'),
    path('events/<int:event_id>/setup/import-team/', views.import_team_csv, name='organizer_import_team_csv'),
    path('events/<int:event_id>/', views.event_detail, name='organizer_event_detail'),
    path('events/<int:event_id>/edit/', views.event_edit, name='organizer_event_edit'),
    path('events/<int:event_id>/delete/', views.event_delete, name='organizer_event_delete'),
    
    # Registration Management URLs
    path('registrations/', views.registration_list, name='organizer_registration_list'),
    path('registrations/export/', views.registration_export, name='organizer_registration_export'),
    path('registrations/bulk-action/', views.registration_bulk_action, name='organizer_registration_bulk_action'),
    path('registrations/badges/print/', views.badge_print_bulk, name='organizer_badge_print_bulk'),
    path('registrations/<int:registration_id>/', views.registration_detail, name='organizer_registration_detail'),
    path('registrations/<int:registration_id>/edit/', views.registration_edit, name='organizer_registration_edit'),
    path('registrations/<int:registration_id>/cancel/', views.registration_cancel, name='organizer_registration_cancel'),
    path('registrations/<int:registration_id>/checkin/', views.registration_checkin, name='organizer_registration_checkin'),
    path('registrations/<int:registration_id>/refund/', views.registration_refund, name='organizer_registration_refund'),
    path('registrations/<int:registration_id>/resend-ticket/', views.registration_resend_ticket, name='organizer_registration_resend_ticket'),
    path('events/<int:event_id>/registrations/', views.event_registration_list, name='organizer_event_registration_list'),
    
    # Communication Management URLs
    path('communication/', views.communication_dashboard, name='organizer_communication_dashboard'),
    path('communication/email-templates/', views.email_template_list, name='organizer_email_template_list'),
    path('communication/email-templates/create/', views.email_template_create, name='organizer_email_template_create'),
    path('communication/email-templates/<int:template_id>/edit/', views.email_template_edit, name='organizer_email_template_edit'),
    path('communication/scheduled-emails/', views.scheduled_email_list, name='organizer_scheduled_email_list'),
    path('communication/scheduled-emails/create/', views.scheduled_email_create, name='organizer_scheduled_email_create'),
    path('communication/scheduled-emails/<int:email_id>/edit/', views.scheduled_email_edit, name='organizer_scheduled_email_edit'),
    path('communication/send-email/', views.send_email, name='organizer_send_email'),
    path('communication/email-logs/', views.email_log_list, name='organizer_email_log_list'),
    path('communication/live-polls/', views.live_poll_list, name='organizer_live_poll_list'),
    path('communication/live-polls/create/', views.live_poll_create, name='organizer_live_poll_create'),
    path('communication/live-polls/<int:poll_id>/', views.live_poll_detail, name='organizer_live_poll_detail'),
    path('communication/live-qa/', views.live_qa_list, name='organizer_live_qa_list'),
    path('communication/live-qa/<int:session_id>/', views.live_qa_session, name='organizer_live_qa_session'),
    
    # Sponsor Management URLs
    path('sponsors/', views.sponsor_list, name='organizer_sponsor_list'),
    path('sponsors/create/', views.sponsor_create, name='organizer_sponsor_create'),
    path('sponsors/<int:sponsor_id>/', views.sponsor_detail, name='organizer_sponsor_detail'),
    path('sponsors/<int:sponsor_id>/edit/', views.sponsor_edit, name='organizer_sponsor_edit'),
    path('sponsors/<int:sponsor_id>/delete/', views.sponsor_delete, name='organizer_sponsor_delete'),
    path('events/<int:event_id>/sponsors/', views.event_sponsor_list, name='organizer_event_sponsor_list'),
    
    # Other URLs
    path('analytics/', views.analytics, name='organizer_analytics'),
    path('analytics/<int:event_id>/', views.analytics, name='organizer_analytics_event'),
    path('team/', views.team_members, name='organizer_team'),
    path('team/<int:member_id>/edit/', views.edit_team_member, name='organizer_edit_team_member'),
    path('templates/', views.templates, name='organizer_templates'),
    path('templates/create/', views.template_create, name='organizer_template_create'),
    path('templates/<int:template_id>/', views.template_detail, name='organizer_template_detail'),
    path('settings/', views.settings, name='organizer_settings'),
    path('notifications/', views.notifications, name='organizer_notifications'),
    path('payouts/', views.payouts, name='organizer_payouts'),
    path('tickets/', views.ticket_management, name='organizer_ticket_management'),
]
