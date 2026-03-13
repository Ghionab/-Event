from django.urls import path
from . import views
from .views_enhanced import (
    enhanced_ticket_purchase, purchase_success, my_purchases, 
    purchase_detail, get_user_info_api, validate_promo_code_api
)
from .views_bulk import (
    bulk_registration_wizard_start, bulk_registration_wizard_mapping,
    bulk_registration_wizard_validation, bulk_registration_wizard_options,
    bulk_registration_wizard_execute, bulk_registration_wizard_results,
    download_error_report, download_template, ajax_validation_preview
)

app_name = 'registration'

urlpatterns = [
    path('', views.registration_list, name='registration_list'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('register/<int:event_id>/', views.register_for_event, name='register_for_event'),
    path('success/<int:registration_id>/', views.registration_success, name='registration_success'),
    path('<int:registration_id>/', views.registration_detail, name='registration_detail'),
    path('<int:registration_id>/cancel/', views.cancel_registration, name='cancel_registration'),
    
    # Enhanced Ticket Purchase URLs
    path('purchase/<int:event_id>/', enhanced_ticket_purchase, name='enhanced_purchase'),
    path('purchase-success/<int:purchase_id>/', purchase_success, name='purchase_success'),
    path('my-purchases/', my_purchases, name='my_purchases'),
    path('purchase/<int:purchase_id>/detail/', purchase_detail, name='purchase_detail'),
    
    # API Endpoints
    path('api/user-info/', get_user_info_api, name='api_user_info'),
    path('api/validate-promo/', validate_promo_code_api, name='api_validate_promo'),
    
    path('ticket/create/<int:event_id>/', views.ticket_create, name='ticket_create'),
    path('ticket/edit/<int:event_id>/<int:ticket_id>/', views.ticket_edit, name='ticket_edit'),
    path('ticket/delete/<int:event_id>/<int:ticket_id>/', views.ticket_delete, name='ticket_delete'),
    path('promo/create/<int:event_id>/', views.promo_code_create, name='promo_code_create'),
    path('promo/validate/', views.promo_code_validate, name='promo_code_validate'),
    path('field/create/<int:event_id>/', views.registration_field_create, name='registration_field_create'),
    path('waitlist/<int:event_id>/<int:ticket_type_id>/', views.add_to_waitlist, name='add_to_waitlist'),
    
    # Phase 4 - Attendee Experience
    path('dashboard/', views.attendee_dashboard, name='attendee_dashboard'),
    path('event/<int:event_id>/<int:registration_id>/', views.attendee_event_detail, name='attendee_event_detail'),
    path('badge/<int:registration_id>/', views.badge_view, name='badge_view'),
    path('badge/<int:registration_id>/print/', views.badge_print, name='badge_print'),
    path('check-in/qr/', views.qr_check_in, name='qr_check_in'),
    path('check-in/manual/<int:event_id>/', views.manual_check_in, name='manual_check_in'),
    path('check-in/<int:registration_id>/', views.perform_check_in, name='perform_check_in'),
    path('preferences/<int:event_id>/', views.attendee_preferences, name='attendee_preferences'),
    path('messages/', views.attendee_messages, name='attendee_messages'),
    path('messages/send/<int:recipient_id>/', views.send_message, name='send_message'),
    path('messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
    path('session/<int:session_id>/feedback/', views.session_feedback, name='session_feedback'),

    # Document Upload URLs
    path('<int:registration_id>/documents/', views.document_list, name='document_list'),
    path('documents/<int:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<int:document_id>/validate/', views.document_validate, name='document_validate'),
    path('documents/<int:document_id>/download/', views.document_download, name='document_download'),
    path('documents/<int:document_id>/delete/', views.document_delete, name='document_delete'),
    path('<int:registration_id>/documents/api/', views.registration_documents_api, name='documents_api'),

    # Legacy Bulk Registration URLs (keep for backward compatibility)
    path('bulk/upload/<int:event_id>/', views.bulk_registration_upload, name='bulk_registration_upload'),
    path('bulk/list/<int:event_id>/', views.bulk_registration_list, name='bulk_registration_list'),
    path('bulk/<int:bulk_id>/', views.bulk_registration_detail, name='bulk_registration_detail'),

    # Enterprise Bulk Registration Wizard URLs
    path('bulk/wizard/<int:event_id>/', bulk_registration_wizard_start, name='bulk_wizard_start'),
    path('bulk/wizard/<int:event_id>/<int:upload_id>/mapping/', bulk_registration_wizard_mapping, name='bulk_wizard_mapping'),
    path('bulk/wizard/<int:event_id>/<int:upload_id>/validation/', bulk_registration_wizard_validation, name='bulk_wizard_validation'),
    path('bulk/wizard/<int:event_id>/<int:upload_id>/options/', bulk_registration_wizard_options, name='bulk_wizard_options'),
    path('bulk/wizard/<int:event_id>/<int:upload_id>/execute/', bulk_registration_wizard_execute, name='bulk_wizard_execute'),
    path('bulk/wizard/<int:event_id>/<int:upload_id>/results/', bulk_registration_wizard_results, name='bulk_wizard_results'),
    
    # Bulk Registration Utilities
    path('bulk/<int:event_id>/<int:upload_id>/error-report/', download_error_report, name='bulk_error_report'),
    path('bulk/<int:event_id>/template/', download_template, name='bulk_template'),
    path('bulk/ajax/<int:event_id>/<int:upload_id>/validation/', ajax_validation_preview, name='ajax_validation_preview'),

    # Manual Registration URLs
    path('manual/create/<int:event_id>/', views.manual_registration_create, name='manual_registration_create'),
    path('manual/list/<int:event_id>/', views.manual_registration_list, name='manual_registration_list'),
    path('manual/edit/<int:event_id>/<int:reg_id>/', views.manual_registration_edit, name='manual_registration_edit'),
    path('manual/delete/<int:event_id>/<int:reg_id>/', views.manual_registration_delete, name='manual_registration_delete'),
    path('manual/send-invite/<int:event_id>/<int:reg_id>/', views.manual_registration_send_invite, name='manual_registration_send_invite'),
    path('manual/create-registration/<int:event_id>/<int:reg_id>/', views.manual_registration_create_registration, name='manual_registration_create_registration'),

    # QR Code Management URLs
    path('qr/<int:event_id>/', views.qr_code_list, name='qr_code_list'),
    path('qr/<int:registration_id>/download/', views.qr_code_download, name='qr_code_download'),
    path('qr/<int:event_id>/print/', views.qr_code_print, name='qr_code_print'),
    path('qr/<int:event_id>/send-emails/', views.qr_code_send_emails, name='qr_code_send_emails'),

    # Bulk Badge Printing URLs
    path('badges/<int:event_id>/print/', views.bulk_badge_print, name='bulk_badge_print'),
    path('badges/<int:event_id>/mark-printed/', views.bulk_badge_mark_printed, name='bulk_badge_mark_printed'),
    path('badges/<int:event_id>/download-pdf/', views.bulk_badge_download_pdf, name='bulk_badge_download_pdf'),

    # Check-in Analytics URLs
    path('check-in/analytics/<int:event_id>/', views.checkin_analytics, name='checkin_analytics'),
    path('check-in/history/<int:event_id>/', views.checkin_history, name='checkin_history'),
    path('check-in/undo/<int:registration_id>/', views.checkin_undo, name='checkin_undo'),
]