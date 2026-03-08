from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def organizer_login(request):
    """Organizer login page - redirects to dashboard if already logged in"""
    if request.user.is_authenticated:
        # Check if user is an organizer
        try:
            from organizers.models import OrganizerProfile
            if hasattr(request.user, 'organizerprofile'):
                return redirect('organizer_dashboard')
            else:
                messages.info(request, 'Please create an organizer profile to access the dashboard.')
                return redirect('organizer_create')
        except:
            return redirect('organizer_dashboard')

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
                    return redirect(next_page)
                else:
                    messages.info(request, 'Please create an organizer profile to access the dashboard.')
                    login(request, user)
                    return redirect('organizer_create')
            except:
                login(request, user)
                return redirect('organizer_dashboard')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')

    return render(request, 'organizers/login.html')


def organizer_logout(request):
    """Logout and redirect to login"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('organizer_login')
