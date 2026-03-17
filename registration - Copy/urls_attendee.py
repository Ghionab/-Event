"""
URL configuration for attendee-specific views
"""
from django.urls import path
from . import views_attendee

app_name = 'attendee'

urlpatterns = [
    # Dashboard
    path('dashboard/', views_attendee.attendee_dashboard, name='dashboard'),

    # Registrations
    path('my-registrations/', views_attendee.my_registrations_enhanced, name='my_registrations'),
    path('registration/<int:registration_id>/', views_attendee.registration_detail_enhanced, name='registration_detail'),
    path('registration/<int:registration_id>/cancel/', views_attendee.cancel_registration_enhanced, name='cancel_registration'),
    path('registration/<int:registration_id>/download-ticket/', views_attendee.download_ticket, name='download_ticket'),

    # Event Discovery
    path('events/search/', views_attendee.event_search, name='event_search'),
    path('events/<int:event_id>/', views_attendee.event_detail_enhanced, name='event_detail'),
    path('events/<int:event_id>/save/', views_attendee.save_event, name='save_event'),
    path('saved-events/', views_attendee.saved_events, name='saved_events'),

    # Schedule
    path('my-schedule/', views_attendee.my_schedule, name='my_schedule'),
    path('schedule/<int:event_id>/', views_attendee.event_schedule, name='event_schedule'),
    path('schedule/export/', views_attendee.export_schedule_ical, name='export_schedule'),
    path('session/<int:session_id>/save/', views_attendee.save_session, name='save_session'),
    path('session/<int:session_id>/feedback/', views_attendee.session_feedback_enhanced, name='session_feedback'),
    path('session/<int:session_id>/add-to-google-calendar/', views_attendee.add_to_google_calendar, name='add_to_google_calendar'),

    # Tickets (accessible to purchaser and attendee)
    path('tickets/', views_attendee.my_tickets, name='my_tickets'),
    path('tickets/<int:registration_id>/preview/', views_attendee.ticket_preview, name='ticket_preview'),

    # Certificates & Post-Event
    path('certificates/', views_attendee.certificates_list, name='certificates'),
    path('certificates/<int:registration_id>/download/', views_attendee.download_certificate, name='download_certificate'),
    path('events/<int:event_id>/materials/', views_attendee.event_materials, name='event_materials'),
    path('events/<int:event_id>/feedback/', views_attendee.event_feedback, name='event_feedback'),

    # Note: Digital badges are available only in the Organizer Portal
    # Badges are created and managed by organizers, not participants

    # Networking
    path('networking/', views_attendee.networking_hub, name='networking_hub'),
    path('networking/attendees/', views_attendee.browse_attendees, name='browse_attendees'),
    path('networking/profile/<int:user_id>/', views_attendee.attendee_profile, name='attendee_profile'),
    path('networking/connect/<int:user_id>/', views_attendee.send_connection_request, name='send_connection_request'),

    # Messages
    path('messages/', views_attendee.messages_enhanced, name='messages'),
    path('messages/send/<int:recipient_id>/', views_attendee.send_message_enhanced, name='send_message'),
    path('messages/<int:message_id>/read/', views_attendee.mark_message_read_enhanced, name='mark_message_read'),

    # Notifications
    path('notifications/', views_attendee.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', views_attendee.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views_attendee.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Preferences
    path('preferences/<int:event_id>/', views_attendee.preferences_enhanced, name='preferences'),
    path('settings/', views_attendee.account_settings, name='settings'),
    path('profile/', views_attendee.attendee_profile_edit, name='profile'),
]
