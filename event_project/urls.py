"""
URL configuration for event_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from organizers import views_auth as organizer_auth_views
from events import views as events_views
from users import views as users_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import JsonResponse
from django.views import View
import sys


class HealthCheckView(View):
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'python_version': sys.version,
            'service': 'eventaxis'
        })


def participant_register_view(request, event_id):
    """Serve the premium participant registration form (participant/register.html)
    for any event. Works for both anonymous and authenticated users.
    The template reads event data via /api/v1/public/events/<id>/ and
    ticket selection from sessionStorage set by the event detail page.
    """
    return render(request, 'participant/register.html', {'event_id': event_id})


@csrf_exempt
def simple_register_api(request):
    """CSRF-exempt public registration API used by participant/register.html.
    Handles: ticket registrations, free events, and waitlist registrations.
    """
    from events_api.views.simple_registration import simple_register
    return simple_register(request)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/security/', include('event_project.admin_urls')),
    path('', events_views.home, name='home'),
    path('events/', include('events.urls')),

    # ── Premium participant registration form ──────────────────────────────
    # Serves participant/register.html with the "For Myself / Someone Else"
    # toggle and ticket summary. Works for anonymous and authenticated users.
    path('events/<int:event_id>/register/', participant_register_view, name='participant_event_register'),
    # ──────────────────────────────────────────────────────────────────────

    path('users/', include('users.urls')),
    path('registration/', include('registration.urls')),
    path('attendee/', include('registration.urls_attendee')),
    path('organizers/', include('organizers.urls')),
    path('coordinators/', include('coordinators.urls')),
    path('staff/', include('staff.urls')),
    path('communication/', include('communication.urls')),
    path('business/', include('business.urls')),
    path('advanced/', include('advanced.urls')),
    path('theming/', include('theming.urls')),
    # Authentication
    path('accounts/login/', users_views.login_view, name='login'),
    path('accounts/logout/', users_views.logout_view, name='logout'),
    path('logout/', users_views.logout_view, name='participant_logout'),
    # Register redirect
    path('register/', RedirectView.as_view(url='/users/register/', permanent=False), name='register_redirect'),
    # API v1
    path('api/v1/', include('events_api.urls')),

    # ── CSRF-exempt registration API (used by participant/register.html) ───
    # Must come AFTER api/v1/ include so it overrides the standard register
    # endpoint with the CSRF-exempt simple_register version.
    path('api/v1/register/', simple_register_api, name='api-simple-register'),
    # ──────────────────────────────────────────────────────────────────────

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health'),
    
    re_path(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

