"""
Gate Staff Portal URLs - Port 8002
Routes for gate staff/bouncer check-in functionality
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from staff import views

urlpatterns = [
    # Redirect root to staff login
    path('', RedirectView.as_view(url='/staff/login/', permanent=False), name='staff_home'),
    
    # Staff authentication
    path('staff/login/', auth_views.LoginView.as_view(
        template_name='staff/login.html',
        redirect_authenticated_user=True,
        extra_context={'next': '/staff/events/'}
    ), name='staff_login'),
    
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    
    # Staff portal routes
    path('staff/', include('staff.urls')),
    
    # API endpoints for check-in
    path('api/v1/', include('events_api.urls')),
    
    # Admin (restricted)
    path('admin/', admin.site.urls),
]

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
