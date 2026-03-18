"""
Coordinator Portal URLs - Port 8003
Routes for event coordinator functionality
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect root to coordinator dashboard or login
    path('', RedirectView.as_view(url='/coordinators/', permanent=False), name='coordinator_root'),
    
    # Coordinator portal routes
    path('coordinators/', include('coordinators.urls')),
    
    # Admin (restricted)
    path('admin/', admin.site.urls),
]

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
