"""
Participant Portal API URLs - No authentication required for public endpoints
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from events_api.views import PublicEventViewSet
from events_api.views.public_registration import public_register, get_user_registrations
from events_api.views.public_tickets import public_create_ticket

router = DefaultRouter()
router.register(r'public/events', PublicEventViewSet, basename='public-event')

urlpatterns = router.urls + [
    # Public registration endpoint (no auth required)
    path('register/', public_register, name='api-public-register'),
    # User registrations (auth required)
    path('registrations/', get_user_registrations, name='api-user-registrations'),
    # Public ticket creation (for testing)
    path('public/tickets/create/', public_create_ticket, name='public-create-ticket'),
]
