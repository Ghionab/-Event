from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import TicketType, PromoCode, Registration, RegistrationField, Waitlist, RegistrationStatus, TicketCategory
from events.models import Event

User = get_user_model()


class TicketTypeModelTest(TestCase):
    """Tests for TicketType model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='organizer'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_create_ticket_type(self):
        """Test creating a ticket type"""
        ticket = TicketType.objects.create(
            event=self.event,
            name='VIP',
            description='VIP Ticket',
            ticket_category=TicketCategory.VIP,
            price=100.00,
            quantity_available=100,
            sales_start=timezone.now(),
            sales_end=timezone.now() + timedelta(days=7)
        )
        self.assertEqual(ticket.name, 'VIP')
        self.assertEqual(ticket.available_quantity, 100)
        self.assertFalse(ticket.is_sold_out)
    
    def test_ticket_sold_out(self):
        """Test ticket sold out status"""
        ticket = TicketType.objects.create(
            event=self.event,
            name='Limited',
            price=50.00,
            quantity_available=10,
            quantity_sold=10,
            sales_start=timezone.now(),
            sales_end=timezone.now() + timedelta(days=7)
        )
        self.assertTrue(ticket.is_sold_out)
        self.assertEqual(ticket.available_quantity, 0)
    
    def test_ticket_can_purchase(self):
        """Test ticket purchase eligibility"""
        ticket = TicketType.objects.create(
            event=self.event,
            name='Available',
            price=50.00,
            quantity_available=10,
            sales_start=timezone.now() - timedelta(days=1),
            sales_end=timezone.now() + timedelta(days=7)
        )
        self.assertTrue(ticket.can_purchase())
        
        # Test inactive ticket
        ticket.is_active = False
        ticket.save()
        self.assertFalse(ticket.can_purchase())
    
    def test_ticket_string(self):
        """Test ticket string representation"""
        ticket = TicketType.objects.create(
            event=self.event,
            name='Test Ticket',
            price=50.00,
            quantity_available=100,
            sales_start=timezone.now(),
            sales_end=timezone.now() + timedelta(days=7)
        )
        self.assertEqual(str(ticket), 'Test Event - Test Ticket')


class PromoCodeModelTest(TestCase):
    """Tests for PromoCode model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_create_promo_code(self):
        """Test creating a promo code"""
        promo = PromoCode.objects.create(
            event=self.event,
            code='SAVE20',
            discount_type='percentage',
            discount_value=20,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30)
        )
        self.assertEqual(promo.code, 'SAVE20')
        self.assertTrue(promo.is_valid())
    
    def test_promo_percentage_discount(self):
        """Test percentage discount calculation"""
        promo = PromoCode.objects.create(
            event=self.event,
            code='SAVE20',
            discount_type='percentage',
            discount_value=20,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30)
        )
        discounted, discount = promo.apply_discount(100.00)
        self.assertEqual(discounted, 80.00)
        self.assertEqual(discount, 20.00)
    
    def test_promo_fixed_discount(self):
        """Test fixed amount discount calculation"""
        promo = PromoCode.objects.create(
            event=self.event,
            code='FLAT10',
            discount_type='fixed',
            discount_value=10,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30)
        )
        discounted, discount = promo.apply_discount(50.00)
        self.assertEqual(discounted, 40.00)
        self.assertEqual(discount, 10.00)
    
    def test_promo_expired(self):
        """Test expired promo code"""
        promo = PromoCode.objects.create(
            event=self.event,
            code='EXPIRED',
            discount_type='percentage',
            discount_value=10,
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(promo.is_valid())
    
    def test_promo_max_uses_reached(self):
        """Test promo code with max uses reached"""
        promo = PromoCode.objects.create(
            event=self.event,
            code='LIMITED',
            discount_type='percentage',
            discount_value=10,
            max_uses=5,
            current_uses=5,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30)
        )
        self.assertFalse(promo.is_valid())


class RegistrationModelTest(TestCase):
    """Tests for Registration model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
        self.ticket = TicketType.objects.create(
            event=self.event,
            name='Regular',
            price=50.00,
            quantity_available=100,
            sales_start=timezone.now(),
            sales_end=timezone.now() + timedelta(days=7)
        )
    
    def test_create_registration(self):
        """Test creating a registration"""
        reg = Registration.objects.create(
            event=self.event,
            user=self.user,
            ticket_type=self.ticket,
            attendee_name='John Doe',
            attendee_email='john@example.com',
            total_amount=50.00
        )
        self.assertIsNotNone(reg.registration_number)
        self.assertTrue(reg.qr_code)
        self.assertEqual(reg.status, RegistrationStatus.CONFIRMED)
    
    def test_registration_confirm(self):
        """Test confirming a registration"""
        reg = Registration.objects.create(
            event=self.event,
            user=self.user,
            ticket_type=self.ticket,
            attendee_name='John Doe',
            attendee_email='john@example.com',
            total_amount=50.00
        )
        initial_sold = self.ticket.quantity_sold
        reg.confirm()
        self.assertEqual(reg.status, RegistrationStatus.CONFIRMED)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.quantity_sold, initial_sold + 1)
    
    def test_registration_cancel(self):
        """Test cancelling a registration"""
        reg = Registration.objects.create(
            event=self.event,
            user=self.user,
            ticket_type=self.ticket,
            attendee_name='John Doe',
            attendee_email='john@example.com',
            total_amount=50.00
        )
        reg.confirm()
        reg.cancel(reason='Changed my mind')
        self.assertEqual(reg.status, RegistrationStatus.CANCELLED)
    
    def test_registration_refund(self):
        """Test refunding a registration"""
        reg = Registration.objects.create(
            event=self.event,
            user=self.user,
            ticket_type=self.ticket,
            attendee_name='John Doe',
            attendee_email='john@example.com',
            total_amount=50.00
        )
        reg.confirm()
        reg.refund(amount=50.00, reason='Event cancelled')
        self.assertEqual(reg.status, RegistrationStatus.REFUNDED)
        self.assertEqual(reg.refund_amount, 50.00)
    
    def test_registration_check_in(self):
        """Test checking in a registration"""
        reg = Registration.objects.create(
            event=self.event,
            user=self.user,
            ticket_type=self.ticket,
            attendee_name='John Doe',
            attendee_email='john@example.com',
            total_amount=50.00
        )
        reg.confirm()
        reg.check_in(checked_by=self.user)
        self.assertEqual(reg.status, RegistrationStatus.CHECKED_IN)
        self.assertIsNotNone(reg.checked_in_at)


class RegistrationFieldModelTest(TestCase):
    """Tests for RegistrationField model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
    
    def test_create_registration_field(self):
        """Test creating a custom registration field"""
        field = RegistrationField.objects.create(
            event=self.event,
            field_name='company',
            field_type='text',
            label='Company Name',
            required=True,
            order=1
        )
        self.assertEqual(field.field_name, 'company')
        self.assertTrue(field.required)
    
    def test_get_options_list(self):
        """Test getting options as list"""
        field = RegistrationField.objects.create(
            event=self.event,
            field_name='diet',
            field_type='select',
            label='Dietary Requirements',
            options='Vegetarian, Vegan, Gluten-Free, None'
        )
        options = field.get_options_list()
        self.assertEqual(options, ['Vegetarian', 'Vegan', 'Gluten-Free', 'None'])


class RegistrationViewsTest(TestCase):
    """Tests for Registration views"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Description',
            status='published',
            is_public=True,
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            organizer=self.user
        )
        self.ticket = TicketType.objects.create(
            event=self.event,
            name='Regular',
            price=50.00,
            quantity_available=100,
            sales_start=timezone.now() - timedelta(days=1),
            sales_end=timezone.now() + timedelta(days=7)
        )
    
    def test_register_view_get(self):
        """Test registration page loads"""
        response = self.client.get(reverse('register_for_event', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')
    
    def test_register_view_post(self):
        """Test successful registration"""
        response = self.client.post(reverse('register_for_event', args=[self.event.id]), {
            'ticket_type': self.ticket.id,
            'attendee_name': 'John Doe',
            'attendee_email': 'john@example.com',
            'attendee_phone': '123-456-7890',
            'special_requests': 'None'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Registration.objects.filter(attendee_email='john@example.com').exists())
    
    def test_registration_detail_requires_login(self):
        """Test registration detail requires login"""
        reg = Registration.objects.create(
            event=self.event,
            user=self.user,
            ticket_type=self.ticket,
            attendee_name='John Doe',
            attendee_email='john@example.com',
            total_amount=50.00
        )
        response = self.client.get(reverse('registration_detail', args=[reg.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_my_registrations_requires_login(self):
        """Test my registrations page requires login"""
        response = self.client.get(reverse('my_registrations'))
        self.assertEqual(response.status_code, 302)
    
    def test_my_registrations_authenticated(self):
        """Test my registrations for authenticated user"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('my_registrations'))
        self.assertEqual(response.status_code, 200)
