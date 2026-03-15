from django.urls import reverse

from users.models import UserRole

from .models import OrganizerProfile


def organizer_profile_exists(user):
    """Return True when the authenticated user already has an organizer profile."""
    if not user or not user.is_authenticated:
        return False
    return OrganizerProfile.objects.filter(user=user).exists()


def ensure_user_is_organizer(user):
    """Promote a user to the organizer role when they create a profile."""
    if not user or not user.is_authenticated:
        return
    if user.role != UserRole.ORGANIZER:
        user.role = UserRole.ORGANIZER
        user.save(update_fields=['role'])


def dashboard_url():
    return reverse('organizers:organizer_dashboard')


def create_url():
    return reverse('organizers:organizer_create')
