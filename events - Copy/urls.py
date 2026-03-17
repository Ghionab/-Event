from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('create/', views.event_create, name='event_create'),
    path('e/<slug:slug>/', views.event_landing, name='event_landing'),
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('<int:event_id>/edit/', views.event_edit, name='event_edit'),
    path('<int:event_id>/delete/', views.event_delete, name='event_delete'),
    
    # Sessions
    path('<int:event_id>/sessions/', views.session_list, name='session_list'),
    path('<int:event_id>/sessions/create/', views.session_create, name='session_create'),
    path('<int:event_id>/sessions/<int:session_id>/edit/', views.session_edit, name='session_edit'),
    path('<int:event_id>/sessions/<int:session_id>/delete/', views.session_delete, name='session_delete'),
    
    # Speakers
    path('<int:event_id>/speakers/', views.speaker_list, name='speaker_list'),
    path('<int:event_id>/speakers/create/', views.speaker_create, name='speaker_create'),
    path('<int:event_id>/speakers/<int:speaker_id>/edit/', views.speaker_edit, name='speaker_edit'),
    path('<int:event_id>/speakers/<int:speaker_id>/delete/', views.speaker_delete, name='speaker_delete'),
    path('<int:event_id>/speakers/<int:speaker_id>/assign/', views.speaker_assign_sessions, name='speaker_assign_sessions'),
    
    # Tracks
    path('<int:event_id>/tracks/', views.track_list, name='track_list'),
    path('<int:event_id>/tracks/create/', views.track_create, name='track_create'),
    path('<int:event_id>/tracks/<int:track_id>/edit/', views.track_edit, name='track_edit'),
    path('<int:event_id>/tracks/<int:track_id>/delete/', views.track_delete, name='track_delete'),
    
    # Rooms
    path('<int:event_id>/rooms/', views.room_list, name='room_list'),
    path('<int:event_id>/rooms/create/', views.room_create, name='room_create'),
    path('<int:event_id>/rooms/<int:room_id>/edit/', views.room_edit, name='room_edit'),
    path('<int:event_id>/rooms/<int:room_id>/delete/', views.room_delete, name='room_delete'),
    
    # Sponsors
    path('<int:event_id>/sponsors/', views.sponsor_list, name='sponsor_list'),
    path('<int:event_id>/sponsors/create/', views.sponsor_create, name='sponsor_create'),
    path('<int:event_id>/sponsors/<int:sponsor_id>/edit/', views.sponsor_edit, name='sponsor_edit'),
    path('<int:event_id>/sponsors/<int:sponsor_id>/delete/', views.sponsor_delete, name='sponsor_delete'),
    
    # Exports
    path('<int:event_id>/export/agenda/', views.export_agenda, name='export_agenda'),
    path('<int:event_id>/export/speakers/', views.export_speakers, name='export_speakers'),
    path('<int:event_id>/export/ical/', views.export_sessions_ical, name='export_sessions_ical'),
]