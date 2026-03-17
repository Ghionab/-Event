"""
REST API endpoints for attendee AJAX functionality
"""
from django.urls import path
from . import api_attendee

app_name = 'attendee_api'

urlpatterns = [
    path('sessions/<int:session_id>/toggle/', api_attendee.toggle_saved_session, name='toggle_session'),
    path('sessions/<int:session_id>/rate/', api_attendee.submit_session_rating, name='rate_session'),
    path('dashboard/', api_attendee.dashboard_data, name='dashboard_data'),
    path('registrations/', api_attendee.registrations_list, name='registrations_list'),
    path('notifications/', api_attendee.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', api_attendee.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', api_attendee.mark_all_read, name='mark_all_read'),
]
