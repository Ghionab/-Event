from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from users.models import UserRole
from .models import OrganizerProfile

User = get_user_model()


class OrganizerLoginFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='organizer@example.com', password='strongpass123')
        self.user.role = UserRole.ORGANIZER
        self.user.save()

    def test_authenticated_organizer_redirects_to_dashboard(self):
        OrganizerProfile.objects.create(user=self.user, company_name='Acme Events')
        self.client.force_login(self.user)
        response = self.client.get(reverse('organizer_login'))
        self.assertRedirects(response, reverse('organizer_dashboard'))

    def test_existing_profile_blocks_create_page(self):
        OrganizerProfile.objects.create(user=self.user, company_name='Acme Events')
        self.client.force_login(self.user)
        response = self.client.get(reverse('organizer_create'))
        self.assertRedirects(response, reverse('organizer_dashboard'))

    def test_login_next_param_pointing_to_create_lands_on_dashboard(self):
        OrganizerProfile.objects.create(user=self.user, company_name='Acme Events')
        response = self.client.post(
            f"{reverse('organizer_login')}?next={reverse('organizer_create')}",
            {'username': self.user.email, 'password': 'strongpass123'}
        )
        self.assertRedirects(response, reverse('organizer_dashboard'))
