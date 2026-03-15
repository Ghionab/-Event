import json
import uuid
import re
from datetime import datetime
from decimal import Decimal
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db import transaction, models
from django.views.decorators.http import require_http_methods
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
    import traceback
    from datetime import datetime

    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'registration_log.txt')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = 'registration_log.txt'
    
    try:
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
                    'event_id': request.POST.get('event_id'),
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

            # Log the incoming request
            with open(log_file, 'a') as f:
                f.write(f'[{timestamp}] RAW_DATA: {data}\n')

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

            # Log parsed data
            with open(log_file, 'a') as f:
                f.write(f'[{timestamp}] PARSED: event_id={event_id} (type={type(event_id).__name__}), email={email}, name={full_name}\n')

            # Create registration
            registration = None
            registration_numbers = []
            total_amount = 0

            if not tickets:
                # Free registration (no tickets available) - create waitlist/interest registration
                reg = Registration.objects.create(
                    event=event,
                    user=attendee_user,
                    purchaser=purchaser,  # Track who made the registration
                    attendee_name=full_name,
                    attendee_email=email,
                    attendee_phone=phone,
                    special_requests=special_requests,
                    total_amount=0,
                    status='waitlisted'  # Waitlisted status - they'll be notified when tickets available
                )
                registration = reg
                registration_numbers.append(reg.registration_number)
                
                # Create notification for the user
                try:
                    from registration.models import AttendeeNotification
                    AttendeeNotification.objects.create(
                        user=attendee_user,
                        notification_type='event_update',
                        title=f"Waitlisted: {event.title}",
                        message=f"You have been added to the waitlist for {event.title}. You will be notified when tickets become available.",
                        related_event=event,
                        link=f"/events/{event.id}/"
                    )
                except Exception:
                    pass  # Notification is optional
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
                        f.write(f'[{timestamp}] DEBUG: ticket_price={ticket_price}, ticket_total={ticket_total}, quantity={quantity}\n')

                    # Create a registration for EACH ticket (quantity can be > 1)
                    for i in range(quantity):
                        reg = Registration.objects.create(
                            event=event,
                            user=attendee_user,
                            purchaser=purchaser,
                            ticket_type=ticket_type,  # CRITICAL: Link the ticket type!
                            attendee_name=full_name,
                            attendee_email=email,
                            attendee_phone=phone,
                            special_requests=special_requests,
                            total_amount=ticket_price,  # Price per ticket
                            status='confirmed'  # Always confirmed until payment integration
                        )
                        registration = reg
                        registration_numbers.append(reg.registration_number)
                        
                        # Log each registration
                        with open(log_file, 'a') as f:
                            f.write(f'[{timestamp}] CREATED_REG: #{reg.registration_number} for ticket {ticket_type.name}\n')
                    
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

            # Send confirmation email with QR code for ALL registrations
            try:
                from registration.views_success import send_qr_email_direct
                # Send email for the last registration (primary one for display)
                if registration:
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
            success_message = 'Registration successful! You will be notified when tickets become available.' if registration.status == 'waitlisted' else 'Registration successful!'
            return HttpResponse(
                json.dumps({
                    'id': registration.id,
                    'registration_number': registration.registration_number,
                    'message': success_message,
                    'status': registration.status,
                    'total_amount': str(total_amount),
                    'success_url': f'/registration/success/{registration.id}/'
                }),
                content_type='application/json'
            )
            
    except Exception as e:
        # Log the full error
        error_trace = traceback.format_exc()
        with open(log_file, 'a') as f:
            f.write(f'[{timestamp}] ERROR: {str(e)}\n')
            f.write(f'[{timestamp}] TRACEBACK: {error_trace}\n')
        
        # Return 500 with the error details for debugging
        return HttpResponse(
            f'Server error: {str(e)}. Check registration_log.txt for details.',
            status=500
        )
