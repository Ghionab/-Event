from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import UserRole

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for custom User model"""
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role=UserRole.ATTENDEE
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.role, UserRole.ATTENDEE)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_organizer(self):
        """Test creating an organizer user"""
        user = User.objects.create_user(
            email='organizer@example.com',
            password='orgpass123',
            role=UserRole.ORGANIZER,
            company='Test Company'
        )
        self.assertEqual(user.role, UserRole.ORGANIZER)
        self.assertEqual(user.company, 'Test Company')
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
    
    def test_user_email_unique(self):
        """Test that email must be unique"""
        User.objects.create_user(
            email='unique@example.com',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='unique@example.com',
                password='testpass123'
            )
    
    def test_user_str(self):
        """Test user string representation"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')
    
    def test_user_role_choices(self):
        """Test user role choices"""
        self.assertEqual(UserRole.ADMIN, 'admin')
        self.assertEqual(UserRole.ORGANIZER, 'organizer')
        self.assertEqual(UserRole.SPEAKER, 'speaker')
        self.assertEqual(UserRole.SPONSOR, 'sponsor')
        self.assertEqual(UserRole.ATTENDEE, 'attendee')


class UserViewsTest(TestCase):
    """Tests for User views"""
    
    def test_register_view_get(self):
        """Test registration page loads"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')
    
    def test_register_view_post(self):
        """Test user registration"""
        response = self.client.post(reverse('register'), {
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'role': 'attendee'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_login_view_get(self):
        """Test login page loads"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
    
    def test_login_view_post_success(self):
        """Test successful login"""
        User.objects.create_user(
            email='login@example.com',
            password='testpass123'
        )
        response = self.client.post(reverse('login'), {
            'email': 'login@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile'))
    
    def test_login_view_post_failure(self):
        """Test failed login"""
        response = self.client.post(reverse('login'), {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')
    
    def test_logout_view(self):
        """Test logout redirects to login"""
        # First login
        User.objects.create_user(
            email='logout@example.com',
            password='testpass123'
        )
        self.client.login(email='logout@example.com', password='testpass123')
        
        # Then logout
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
    
    def test_profile_view_requires_login(self):
        """Test profile page requires authentication"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
    
    def test_profile_view_authenticated(self):
        """Test profile page for authenticated user"""
        user = User.objects.create_user(
            email='profile@example.com',
            password='testpass123'
        )
        self.client.login(email='profile@example.com', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'profile@example.com')
    
    def test_password_reset_view(self):
        """Test password reset page loads"""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password Reset')
