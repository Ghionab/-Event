from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('', views.registration_list, name='registration_list'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('register/<int:event_id>/', views.register_for_event, name='register_for_event'),
    path('<int:registration_id>/', views.registration_detail, name='registration_detail'),
    path('<int:registration_id>/cancel/', views.cancel_registration, name='cancel_registration'),
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

    # Bulk Registration URLs
    path('bulk/upload/<int:event_id>/', views.bulk_registration_upload, name='bulk_registration_upload'),
    path('bulk/list/<int:event_id>/', views.bulk_registration_list, name='bulk_registration_list'),
    path('bulk/<int:bulk_id>/', views.bulk_registration_detail, name='bulk_registration_detail'),

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

    # Check-in Analytics URLs
    path('check-in/analytics/<int:event_id>/', views.checkin_analytics, name='checkin_analytics'),
    path('check-in/history/<int:event_id>/', views.checkin_history, name='checkin_history'),
    path('check-in/undo/<int:registration_id>/', views.checkin_undo, name='checkin_undo'),
]