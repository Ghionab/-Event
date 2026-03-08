"""
Participant Portal URLs - Port 8001
Public-facing routes for event attendees
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

# Simple CSRF exempt registration API
@csrf_exempt
def simple_register_api(request):
    from events_api.views.simple_registration import simple_register
    return simple_register(request)

def participant_register(request, event_id):
    """Render registration page with event_id"""
    return TemplateView.as_view(
        template_name='participant/register_simple.html'
    )(request, event_id=event_id)


def participant_logout(request):
    """Simple logout view that logs out and redirects to login"""
    from django.contrib.auth import logout
    logout(request)
    return RedirectView.as_view(url='/login/')(request)


def participant_signup(request):
    """Simple signup view for participants"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        errors = []

        if not email:
            errors.append('Email is required')
        if not first_name:
            errors.append('First name is required')
        if not last_name:
            errors.append('Last name is required')
        if not password1:
            errors.append('Password is required')
        if password1 != password2:
            errors.append('Passwords do not match')
        if len(password1) < 8:
            errors.append('Password must be at least 8 characters')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists')

        if errors:
            # Re-render form with errors
            from django.shortcuts import render
            return render(request, 'participant/signup.html', {
                'form_errors': errors,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            })

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            role='attendee',  # Set role to attendee
        )

        # Log the user in
        from django.contrib.auth import authenticate, login
        user = authenticate(request, username=email, password=password1)
        if user:
            login(request, user)
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/')

        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/login/')

    # GET request - show form
    from django.shortcuts import render
    return render(request, 'participant/signup.html', {})


urlpatterns = [
    # Home - Participant landing page
    path('', TemplateView.as_view(template_name='participant/home.html'), name='participant_home'),

    # Event listing (public)
    path('events/', TemplateView.as_view(template_name='participant/events.html'), name='participant_events'),

    # Registration flow - MUST come before event detail
    path('events/<int:event_id>/register/', participant_register, name='participant_register'),

    # Event detail (public view - no registration)
    path('events/<int:event_id>/', TemplateView.as_view(template_name='participant/event_detail.html'), name='participant_event_detail'),

    # Event detail with slug
    path('events/<int:event_id>/<slug:slug>/', TemplateView.as_view(template_name='participant/event_detail.html'), name='participant_event_detail_slug'),

    # My registrations (auth required)
    path('my-registrations/', TemplateView.as_view(template_name='participant/my_registrations.html'), name='participant_my_registrations'),

    # Single registration detail
    path('my-registrations/<int:registration_id>/', TemplateView.as_view(template_name='participant/registration_detail.html'), name='participant_registration_detail'),

    # User authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='participant/login.html',
        redirect_authenticated_user=True
    ), name='participant_login'),

    path('logout/', participant_logout, name='participant_logout'),

    path('register/', participant_signup, name='participant_signup'),

    # Password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='participant/password_reset.html'
    ), name='participant_password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='participant/password_reset_done.html'
    ), name='participant_password_reset_done'),

    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='participant/password_reset_confirm.html'
    ), name='participant_password_reset_confirm'),

    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='participant/password_reset_complete.html'
    ), name='participant_password_reset_complete'),

    # User profile
    path('profile/', TemplateView.as_view(template_name='participant/profile.html'), name='participant_profile'),

    # Django auth URLs with accounts/ prefix
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='participant/login.html',
        redirect_authenticated_user=True
    ), name='account_login'),

    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='/login/'
    ), name='account_logout'),

    path('accounts/signup/', participant_signup, name='account_signup'),

    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='participant/password_reset.html'
    ), name='account_password_reset'),

    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='participant/password_reset_done.html'
    ), name='account_password_reset_done'),

    path('accounts/password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='participant/password_reset_confirm.html'
    ), name='account_password_reset_confirm'),

    path('accounts/password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='participant/password_reset_complete.html'
    ), name='account_password_reset_complete'),

    path('accounts/profile/', RedirectView.as_view(url='/profile/', permanent=True), name='account_profile'),

    # API endpoints (public) - participant specific, must come first
    path('api/v1/', include('events_api.urls_participant')),
    # Simple registration API - completely CSRF exempt
    path('api/v1/register/', simple_register_api, name='api-public-register'),
    # Include main API for tickets (GET)
    path('api/v1/', include('events_api.urls')),

    # API Documentation (read-only for participants)
    path('api/docs/', TemplateView.as_view(template_name='participant/api_docs.html'), name='participant_api_docs'),

    # Attendee portal routes (authenticated)
    path('attendee/', include('registration.urls_attendee')),

    # Attendee API endpoints
    path('api/attendee/', include('registration.urls_api_attendee')),
]

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
