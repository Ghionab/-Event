"""
Simple public registration API for participant portal
"""
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction, models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db.models import Q, F
from events.models import Event
from registration.models import Registration, TicketType

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_registrations(request):
    """Get all registrations for the current user"""
    registrations = Registration.objects.filter(
        Q(user=request.user) | Q(attendee_email__iexact=request.user.email)
    ).select_related('event', 'ticket_type').order_by('-created_at')

    data = []
    for reg in registrations:
        data.append({
            'id': reg.id,
            'registration_number': reg.registration_number,
            'event_id': reg.event.id if reg.event else None,
            'event_title': reg.event.title if reg.event else 'Unknown Event',
            'event_date': reg.event.start_date if reg.event else None,
            'event_venue': reg.event.venue_name if reg.event else '',
            'ticket_type_name': reg.ticket_type.name if reg.ticket_type else 'General Admission',
            'status': reg.status,
            'created_at': reg.created_at,
        })

    return Response(data)


from rest_framework.decorators import api_view, permission_classes, authentication_classes

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
@transaction.atomic
def public_register(request):
    """Public endpoint for event registration without authentication"""
    import re
    import os
    from datetime import datetime

    # Log raw request data for debugging
    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'registration_log.txt')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Get raw data for logging
    raw_data = request.data if hasattr(request, 'data') else {}
    raw_str = str(raw_data)[:200]
    with open(log_file, 'a') as f:
        f.write(f'[{timestamp}] RAW_DATA: {raw_str}\n')

    event_id = request.data.get('event_id')
    full_name = request.data.get('full_name', '')
    email = request.data.get('email', '')
    phone = request.data.get('phone', '')
    special_requests = request.data.get('special_requests', '')
    tickets = request.data.get('tickets', [])

    # Log received values
    with open(log_file, 'a') as f:
        f.write(f'[{timestamp}] PARSED: event_id={event_id} (type={type(event_id).__name__}), email={email}, name={full_name}\n')

    if not event_id:
        msg = f'[{timestamp}] FAILED | Empty event_id received'
        with open(log_file, 'a') as f:
            f.write(msg + '\n')
        return Response({'error': 'Event ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not email:
        msg = f'[{timestamp}] FAILED | Email is required for event_id={event_id}'
        with open(log_file, 'a') as f:
            f.write(msg + '\n')
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        msg = f'[{timestamp}] FAILED | Invalid email format: {email}'
        with open(log_file, 'a') as f:
            f.write(msg + '\n')
        return Response({'error': 'Please enter a valid email address'}, status=status.HTTP_400_BAD_REQUEST)

    # Get event - convert event_id to int
    try:
        event_id_int = int(event_id)
        event = Event.objects.get(id=event_id_int, is_public=True, status='published')
    except (Event.DoesNotExist, ValueError) as e:
        msg = f'[{timestamp}] FAILED | Event not found: event_id={event_id}, error={str(e)}'
        with open(log_file, 'a') as f:
            f.write(msg + '\n')
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

    # If no tickets provided, create a basic registration
    if not tickets:
        reg = Registration.objects.create(
            event=event,
            user=user,
            attendee_name=full_name,
            attendee_email=email,
            attendee_phone=phone,
            special_requests=special_requests,
            status='confirmed'
        )
        registration = reg
        registration_numbers.append(reg.registration_number)
    else:
        for ticket_data in tickets:
            ticket_id = ticket_data.get('ticket_id')
            quantity = ticket_data.get('quantity', 1)

            try:
                ticket_type = TicketType.objects.select_for_update().get(id=ticket_id, event=event, is_active=True)
            except TicketType.DoesNotExist:
                continue

            # Check availability
            if ticket_type.available_quantity < quantity:
                # Return error if any ticket in the batch is unavailable
                return Response({'error': f'Ticket finished for {ticket_type.name}'}, status=status.HTTP_400_BAD_REQUEST)

            reg = Registration.objects.create(
                event=event,
                user=user,
                ticket_type=ticket_type,
                attendee_name=full_name,
                attendee_email=email,
                attendee_phone=phone,
                special_requests=special_requests,
                status='confirmed'  # Always confirmed until payment integration
            )
            registration_numbers.append(reg.registration_number)

            # Update quantity sold and available atomically
            ticket_type.quantity_sold += quantity
            ticket_type.quantity_available -= quantity
            ticket_type.save()

            if registration is None:
                registration = reg

    if not registration_numbers:
        msg = f'[{timestamp}] FAILED | No tickets available for event_id={event_id}'
        with open(log_file, 'a') as f:
            f.write(msg + '\n')
        return Response({'error': 'No tickets available or invalid tickets'}, status=status.HTTP_400_BAD_REQUEST)

    # Log successful registration
    msg = f'[{timestamp}] SUCCESS | event_id={event_id} | name={full_name} | email={email} | status={registration.status} | reg#={registration.registration_number}'
    with open(log_file, 'a') as f:
        f.write(msg + '\n')

    return Response({
        'id': registration.id,
        'registration_number': registration.registration_number,
        'message': 'Registration successful!',
        'status': registration.status
    })
