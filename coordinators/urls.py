from django.urls import path
from . import views

app_name = 'coordinators'

urlpatterns = [
    # Authentication - make login the default
    path('', views.coordinator_login, name='coordinator_login'),
    path('login/', views.coordinator_login, name='coordinator_login'),
    path('logout/', views.coordinator_logout, name='coordinator_logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Events
    path('events/', views.event_list, name='event_list'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/edit/', views.event_edit, name='event_edit'),
    
    # Event Management
    path('events/<int:event_id>/sessions/', views.session_list, name='session_list'),
    path('events/<int:event_id>/speakers/', views.speaker_list, name='speaker_list'),
    path('events/<int:event_id>/sponsors/', views.sponsor_list, name='sponsor_list'),
    path('events/<int:event_id>/communications/', views.communications, name='communications'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytics'),
]
