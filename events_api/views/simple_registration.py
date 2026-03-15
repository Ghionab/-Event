import json
import uuid
import re
from datetime import datetime
from decimal import Decimal
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db import transaction, models
from events.models import Event
from registration.models import Registration, TicketType, RegistrationStatus
from django.contrib.auth import get_user_model

User = get_user_model()

@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def simple_register(request):
    """Simple public registration endpoint without authentication"""
    import re
    import os
    from datetime import datetime

    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'registration_log.txt')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = 'registration_log.txt'
    
    # Identify content type
    content_type = request.META.get('CONTENT_TYPE', '')
    
    if request.method == 'POST':
        if 'application/json' in content_type:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return HttpResponse('Invalid JSON', status=400)
        else:
            # Handle form data
            tickets_raw = request.POST.get('tickets', '[]')
            try:
                tickets = json.loads(tickets_raw)
            except json.JSONDecodeError:
                tickets = []
                
            data = {
                'event_id': request.POST.get('event_id') or event_id,
                'full_name': request.POST.get('full_name', ''),
                'email': request.POST.get('email', ''),
                'phone': request.POST.get('phone', ''),
                'special_requests': request.POST.get('special_requests', ''),
                'tickets': tickets,
                'for_myself': request.POST.get('for_myself') == 'true',
            }

        event_id = data.get('event_id')
        full_name = data.get('full_name', '')
        email = data.get('email', '')
        phone = data.get('phone', '')
        special_requests = data.get('special_requests', '')
        tickets = data.get('tickets', [])
        is_for_self = data.get('for_myself', True)

        if not event_id:
            return HttpResponse('Event ID is required', status=400)
        if not email:
            return HttpResponse('Email is required', status=400)

        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return HttpResponse('Please enter a valid email address', status=400)

        # Get event
        try:
            event = Event.objects.get(id=int(event_id), is_public=True, status='published')
        except (Event.DoesNotExist, ValueError):
            return HttpResponse('Event not found', status=404)

        # Identify purchaser and attendee
        # Explicitly get user if request.user is not authenticated
        from django.contrib.auth import get_user
        purchaser = request.user if request.user.is_authenticated else get_user(request)
        if not purchaser.is_authenticated:
            purchaser = None
        
        # Identify attendee user (the one the ticket is for)
        # Find or create attendee user by email
        attendee_user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': full_name.split()[0] if full_name else '',
                'last_name': ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
            }
        )

    # Create registration
    registration = None
    registration_numbers = []
    total_amount = 0

    if not tickets:
        # Free registration
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
    else:
        # Paid registration
        for ticket_data in tickets:
            ticket_id = ticket_data.get('ticket_id')
            quantity = int(ticket_data.get('quantity', 1))

            try:
                ticket_type = TicketType.objects.select_for_update().get(id=ticket_id, event=event, is_active=True)
            except TicketType.DoesNotExist:
                continue

            if ticket_type.quantity_available < quantity:
                return HttpResponse(f'Ticket "{ticket_type.name}" is finished', status=400)

            # Use Decimal for currency
            ticket_price = ticket_type.price if ticket_type.price else Decimal('0')
            ticket_total = ticket_price * quantity
            total_amount += ticket_total

            # DEBUG
            with open(log_file, 'a') as f:
                f.write(f'[{timestamp}] DEBUG: ticket_price={ticket_price}, ticket_total={ticket_total}\n')

            reg = Registration.objects.create(
                event=event,
                user=attendee_user,
                purchaser=purchaser,
                attendee_name=full_name,
                attendee_email=email,
                attendee_phone=phone,
                special_requests=special_requests,
                total_amount=ticket_total,
                status='confirmed'  # Always confirmed until payment integration
            )
            registration = reg
            registration_numbers.append(reg.registration_number)
            
            # Atomic updates
            ticket_type.quantity_sold += quantity
            ticket_type.quantity_available -= quantity
            ticket_type.save()

            if registration is None:
                registration = reg

    if not registration_numbers:
        return HttpResponse('Please select at least one valid ticket to complete registration.', status=400)

    # Log success
    with open(log_file, 'a') as f:
        f.write(f'[{timestamp}] SUCCESS: reg#={registration.registration_number}, amount=${total_amount}\n')

    # Send confirmation email with QR code
    try:
        from registration.views_success import send_qr_email_direct
        send_qr_email_direct(registration)
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f'[{timestamp}] EMAIL ERROR: {str(e)}\n')

    # Log content type for debugging
    with open(log_file, 'a') as f:
        f.write(f'[{timestamp}] CONTENT_TYPE: {content_type}\n')
        f.write(f'[{timestamp}] REDIRECT: /registration/success/{registration.id}/\n')

    # For form submissions, redirect to success page
    if 'application/json' not in content_type:
        return HttpResponseRedirect(f'/registration/success/{registration.id}/')

    # For JSON requests
    return HttpResponse(
        json.dumps({
            'id': registration.id,
            'registration_number': registration.registration_number,
            'message': 'Registration successful!',
            'status': registration.status,
            'total_amount': str(total_amount),
            'success_url': f'/registration/success/{registration.id}/'
        }),
        content_type='application/json'
    )
