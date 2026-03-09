from django.urls import path, include
from rest_framework.routers import DefaultRouter

from events_api.views import (
    LoginView, LogoutView, UserDetailView, UserCreateView,
    EventViewSet, TrackViewSet, RoomViewSet, SponsorViewSet,
    SpeakerViewSet, SessionViewSet,
    VendorViewSet, ContractViewSet,
    TicketTypeViewSet, PromoCodeViewSet, RegistrationViewSet,
    PublicRegisterView, SendQREmailView
)

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='api-event')
router.register(r'vendors', VendorViewSet, basename='api-vendor')

urlpatterns = [
    # Authentication
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('auth/user/', UserDetailView.as_view(), name='api-user'),
    path('auth/register/', UserCreateView.as_view(), name='api-register'),

    # Events
    path('', include(router.urls)),

    # Event-specific resources
    path('events/<int:event_pk>/tracks/', TrackViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-event-tracks'),
    path('events/<int:event_pk>/tracks/<int:pk>/', TrackViewSet.as_view({'put': 'update', 'delete': 'destroy'}), name='api-event-track-detail'),

    path('events/<int:event_pk>/rooms/', RoomViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-event-rooms'),
    path('events/<int:event_pk>/rooms/<int:pk>/', RoomViewSet.as_view({'put': 'update', 'delete': 'destroy'}), name='api-event-room-detail'),

    path('events/<int:event_pk>/sponsors/', SponsorViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-event-sponsors'),
    path('events/<int:event_pk>/sponsors/<int:pk>/', SponsorViewSet.as_view({'put': 'update', 'delete': 'destroy'}), name='api-event-sponsor-detail'),

    path('events/<int:event_pk>/speakers/', SpeakerViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-event-speakers'),
    path('events/<int:event_pk>/speakers/<int:pk>/', SpeakerViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='api-event-speaker-detail'),

    path('events/<int:event_pk>/sessions/', SessionViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-event-sessions'),
    path('events/<int:event_pk>/sessions/<int:pk>/', SessionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='api-event-session-detail'),

    path('events/<int:event_pk>/tickets/', TicketTypeViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-event-tickets'),
    path('events/<int:event_pk>/promocodes/', PromoCodeViewSet.as_view({'get': 'list'}), name='api-event-promocodes'),
    path('events/<int:event_pk>/promocodes/validate/', PromoCodeViewSet.as_view({'post': 'validate'}), name='api-event-promocode-validate'),
    path('events/<int:event_pk>/registrations/', RegistrationViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-event-registrations'),
    path('events/<int:event_pk>/registrations/<int:pk>/', RegistrationViewSet.as_view({'get': 'retrieve'}), name='api-event-registration-detail'),
    path('events/<int:event_pk>/registrations/<int:pk>/cancel/', RegistrationViewSet.as_view({'post': 'cancel'}), name='api-event-registration-cancel'),
    path('events/<int:event_pk>/registrations/<int:pk>/check-in/', RegistrationViewSet.as_view({'post': 'check_in'}), name='api-event-registration-checkin'),

    # Public registration endpoint
    path('register/', PublicRegisterView.as_view(), name='api-public-register'),
    
    # QR code email endpoint
    path('send-qr-email/', SendQREmailView, name='api-send-qr-email'),

    path('events/<int:event_pk>/contracts/', ContractViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-event-contracts'),
    path('events/<int:event_pk>/contracts/<int:pk>/', ContractViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='api-event-contract-detail'),
]
