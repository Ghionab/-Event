from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .utils import (
    organizer_profile_exists, dashboard_url, create_url
)


def _resolve_next_login_url(next_param):
    default = dashboard_url()
    if not next_param:
        return default
    try:
        resolved = resolve_url(next_param)
    except Exception:
        return default
    return resolved if resolved.rstrip('/') != create_url().rstrip('/') else default


@require_http_methods(["GET", "POST"])
def organizer_login(request):
    """Organizer login page - redirects to dashboard if already logged in."""
    if request.user.is_authenticated:
        if organizer_profile_exists(request.user):
            return redirect(dashboard_url())
        messages.info(request, 'Please create an organizer profile to access the dashboard.')
        return redirect(create_url())

    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            # Check if user has organizer profile
            try:
                from organizers.models import OrganizerProfile
                if hasattr(user, 'organizerprofile'):
                    login(request, user)
                    next_page = request.GET.get('next', '/organizers/')
                    # Validate next parameter to prevent open redirects
                    if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                        return redirect(next_page)
                    else:
                        return redirect('/organizers/')
                else:
                    messages.info(request, 'Please create an organizer profile to access the dashboard.')
                    login(request, user)
                    return redirect('organizers:organizer_create')
            except:
                login(request, user)
                return redirect('organizers:organizer_dashboard')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')

    return render(request, 'organizers/login.html')


def organizer_logout(request):
    """Logout and redirect to login"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('organizers:organizer_login')
