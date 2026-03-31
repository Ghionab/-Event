from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy

# Create your views here.

def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password1', '')
        password_confirm = request.POST.get('password2', '')
        role = request.POST.get('role', 'attendee')
        
        errors = []
        if not email or not password:
            errors.append("Email and password are required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password != password_confirm:
            errors.append("Passwords do not match.")
            
        if not errors:
            from .models import User, UserRole
            if User.objects.filter(email=email).exists():
                errors.append("Email address is already registered.")
            else:
                user_role = UserRole.ORGANIZER if role == 'organizer' else UserRole.ATTENDEE
                
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=user_role
                )
                
                if user_role == UserRole.ORGANIZER:
                    # Auto-create the OrganizerProfile to streamline onboarding
                    from organizers.models import OrganizerProfile
                    OrganizerProfile.objects.get_or_create(
                        user=user,
                        defaults={'company_name': f"{first_name} {last_name}'s Events" if first_name else "My Events"}
                    )
                    messages.success(request, 'Organizer Account created successfully! Please log in.')
                else:
                    messages.success(request, 'Account created successfully! Please log in to discover events.')
                    
                return redirect('login')
                
        return render(request, 'users/register.html', {
            'form_errors': errors,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'selected_role': role,
        })
        
    # Read ?role= from URL to pre-select the role card
    selected_role = request.GET.get('role', 'attendee')
    return render(request, 'users/register.html', {'selected_role': selected_role})
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                
                # Role-based redirection logic
                from users.models import UserRole
                
                # Check for standard next parameter
                next_page = request.GET.get('next')
                if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                    return redirect(next_page)
                
                if user.role == UserRole.ORGANIZER:
                    return redirect('organizers:organizer_dashboard')
                elif user.role == 'coordinator':
                    return redirect('coordinators:dashboard')
                elif user.role in [UserRole.STAFF, UserRole.USHER]:
                    return redirect('staff:event_list')
                elif user.role == UserRole.ATTENDEE:
                    return redirect('attendee:dashboard')
                elif user.is_staff or user.is_superuser or user.role == UserRole.ADMIN:
                    return redirect('/admin/')
                else:
                    return redirect('profile')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

@login_required
def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})


class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Password Reset'
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Password Reset Email Sent'
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Reset Password'
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Password Reset Complete'
        return context
