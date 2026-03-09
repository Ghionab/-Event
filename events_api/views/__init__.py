# Authentication Views
from events_api.views.auth_views import LoginView, LogoutView, UserDetailView, UserCreateView, UserUpdateView

# Event Views
from events_api.views.event_views import EventViewSet, TrackViewSet, RoomViewSet, SponsorViewSet

# Speaker Views
from events_api.views.speaker_views import SpeakerViewSet

# Session Views
from events_api.views.session_views import SessionViewSet

# Vendor Views
from events_api.views.vendor_views import VendorViewSet, ContractViewSet

# Registration Views
from events_api.views.registration_views import TicketTypeViewSet, PromoCodeViewSet, RegistrationViewSet, PublicRegisterView, SendQREmailView

# Public Views (for participant portal - no auth required)
from events_api.views.public_views import PublicEventViewSet
