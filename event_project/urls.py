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
from organizers import views_auth as organizer_auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/security/', include('event_project.admin_urls')),
    path('', RedirectView.as_view(url='/organizers/login/', permanent=False), name='home'),
    path('events/', include('events.urls')),
    path('users/', include('users.urls')),
    path('registration/', include('registration.urls')),
    path('attendee/', include('registration.urls_attendee')),
    path('organizers/', include('organizers.urls')),
    path('communication/', include('communication.urls')),
    path('business/', include('business.urls')),
    path('advanced/', include('advanced.urls')),
    path('theming/', include('theming.urls')),
    # Authentication
    path('accounts/login/', organizer_auth_views.organizer_login, name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/organizers/login/'), name='logout'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/organizers/login/', http_method_names=['get', 'post']), name='participant_logout'),
    # Register redirect
    path('register/', RedirectView.as_view(url='/organizers/create/', permanent=False), name='register_redirect'),
    # API v1
    path('api/v1/', include('events_api.urls')),
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    re_path(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
