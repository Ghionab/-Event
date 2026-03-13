from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone

from registration.models import Registration, TicketType, PromoCode
from events_api.serializers import (
    RegistrationSerializer, RegistrationCreateSerializer,
    TicketTypeSerializer, PromoCodeSerializer
)
from events_api.permissions import IsParticipant, IsRegistrationOwner


class TicketTypeViewSet(viewsets.ModelViewSet):
    serializer_class = TicketTypeSerializer
    permission_classes = [IsParticipant]

    def get_queryset(self):
        event_id = self.kwargs.get('event_pk')
        return TicketType.objects.filter(event_id=event_id, is_active=True)

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_pk')
        serializer.save(event_id=event_id)


class PromoCodeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PromoCodeSerializer
    permission_classes = [IsParticipant]

    def get_queryset(self):
        event_id = self.kwargs.get('event_pk')
        return PromoCode.objects.filter(event_id=event_id, is_active=True)

    @action(detail=False, methods=['post'])
    def validate(self, request, event_pk=None):
        code = request.data.get('code', '').upper()
        try:
            promo = PromoCode.objects.get(code=code, event_id=event_pk, is_active=True)
            if promo.is_valid():
                return Response({
                    'valid': True,
                    'code': promo.code,
                    'discount_type': promo.discount_type,
                    'discount_value': promo.discount_value
                })
            return Response({'valid': False, 'error': 'Promo code is expired or max uses reached'})
        except PromoCode.DoesNotExist:
            return Response({'valid': False, 'error': 'Invalid promo code'})


class RegistrationViewSet(viewsets.ModelViewSet):
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return RegistrationCreateSerializer
        return RegistrationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['organizer', 'admin', 'staff']:
            event_id = self.kwargs.get('event_pk')
            if event_id:
                return Registration.objects.filter(event_id=event_id)
            return Registration.objects.all()
        return Registration.objects.filter(user=user)

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_pk')
        serializer.save(event_id=event_id)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None, event_pk=None):
        registration = self.get_object()
        if registration.status != 'confirmed':
            return Response(
                {'error': 'Cannot cancel this registration'},
                status=status.HTTP_400_BAD_REQUEST
            )
        registration.status = 'cancelled'
        registration.save()
        return Response({'message': 'Registration cancelled', 'status': registration.status})

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None, event_pk=None):
        from registration.models import CheckIn, RegistrationStatus
        
        registration = self.get_object()
        
        # Check if already checked in
        if registration.status == RegistrationStatus.CHECKED_IN:
            return Response({
                'error': f'{registration.attendee_name} is already checked in',
                'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None
            })
        
        # Check if registration is confirmed
        if registration.status != RegistrationStatus.CONFIRMED:
            return Response({
                'error': f'Registration status is {registration.get_status_display()}. Only confirmed registrations can be checked in.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform check-in
        checked_by = request.user if request.user.is_authenticated else None
        success = registration.check_in(checked_by=checked_by)
        
        if success:
            # Log check-in
            CheckIn.objects.create(
                registration=registration,
                checked_in_by=checked_by,
                method='qr_scan',
                notes='QR code scan via staff portal API'
            )
            
            return Response({
                'success': True,
                'message': f'{registration.attendee_name} checked in successfully',
                'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None,
                'registration': {
                    'id': registration.id,
                    'attendee_name': registration.attendee_name,
                    'status': registration.status
                }
            })
        else:
            return Response({
                'error': 'Check-in failed. Registration must be confirmed.'
            }, status=status.HTTP_400_BAD_REQUEST)


from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import base64
import io

@api_view(['POST'])
@permission_classes([AllowAny])
def SendQREmailView(request):
    """Send QR code via email"""
    try:
        registration_id = request.data.get('registration_id')
        
        if not registration_id:
            return Response({'success': False, 'error': 'Registration ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get registration
        try:
            registration = Registration.objects.get(id=registration_id)
        except Registration.DoesNotExist:
            return Response({'success': False, 'error': 'Registration not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate QR code
        qr_image = registration.generate_qr_code_image()
        
        # Create email content
        subject = f'Your QR Code for {registration.event.title}'
        
        html_message = render_to_string('registration/qr_email.html', {
            'registration': registration,
            'event': registration.event,
            'qr_image': qr_image
        })
        
        # Send email
        send_mail(
            subject=subject,
            message='',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@eventportal.com'),
            recipient_list=[registration.attendee_email],
            html_message=html_message,
            fail_silently=False
        )
        
        return Response({'success': True, 'message': 'QR code sent successfully'})
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PublicRegisterView(APIView):
    """Public registration endpoint without authentication"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """Handle public event registration"""
        from django.contrib.auth import get_user_model
        from events.models import Event

        User = get_user_model()

        event_id = request.data.get('event_id')
        full_name = request.data.get('full_name', '')
        email = request.data.get('email', '')
        phone = request.data.get('phone', '')
        special_requests = request.data.get('special_requests', '')
        tickets = request.data.get('tickets', [])

        if not event_id:
            return Response({'error': 'Event ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get event
        try:
            event = Event.objects.get(id=event_id, is_public=True, status='published')
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        # Find or create user by email
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': full_name.split()[0] if full_name else '',
                'last_name': ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
            }
        )

        # Create registration
        registration = None
        registration_numbers = []

        for ticket_data in tickets:
            ticket_id = ticket_data.get('ticket_id')
            quantity = ticket_data.get('quantity', 1)

            try:
                ticket_type = TicketType.objects.get(id=ticket_id, event=event, is_active=True)
            except TicketType.DoesNotExist:
                continue

            # Check availability
            available = ticket_type.quantity_available - ticket_type.quantity_sold
            if available < quantity:
                continue

            # Calculate ticket total
            ticket_price = ticket_type.price if ticket_type.price else Decimal('0')
            ticket_total = ticket_price * quantity

            reg = Registration.objects.create(
                event=event,
                user=user,
                ticket_type=ticket_type,
                attendee_name=full_name,
                attendee_email=email,
                attendee_phone=phone,
                special_requests=special_requests,
                total_amount=ticket_total,
                status='confirmed' if ticket_price == 0 else 'pending'
            )
            registration_numbers.append(reg.registration_number)

            # Update quantity sold
            ticket_type.quantity_sold += quantity
            ticket_type.save()

            if registration is None:
                registration = reg

        # If no tickets provided or no valid tickets, create a basic registration
        if not tickets or not registration_numbers:
            reg = Registration.objects.create(
                event=event,
                user=user,
                attendee_name=full_name,
                attendee_email=email,
                attendee_phone=phone,
                special_requests=special_requests,
                total_amount=0,
                status='confirmed'
            )
            registration = reg
            registration_numbers.append(reg.registration_number)

        if not registration_numbers:
            return Response({'error': 'No tickets available or invalid tickets'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total for response
        total = sum(
            (TicketType.objects.get(id=t['ticket_id']).price or Decimal('0')) * t.get('quantity', 1)
            for t in tickets
            if t.get('ticket_id')
        ) if tickets else Decimal('0')

        return Response({
            'id': registration.id,
            'registration_number': registration.registration_number,
            'message': 'Registration successful!',
            'status': registration.status,
            'total_amount': float(registration.total_amount) if registration.total_amount else 0
        })
