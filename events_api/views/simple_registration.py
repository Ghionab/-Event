import json
import uuid
import re
from datetime import datetime
from decimal import Decimal
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import models
from django.conf import settings
from events.models import Event
from registration.models import Registration, TicketType, RegistrationStatus
from django.contrib.auth import get_user_model

User = get_user_model()

@csrf_exempt
def simple_register(request, event_id=None):
    """Simple registration view for form or JSON submissions"""
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

        # LOGGING FOR DEBUGGING
        with open('registration_auth_debug.log', 'a') as f:
            f.write(f"[{timestamp}] User Authenticated: {request.user.is_authenticated}\n")
            f.write(f"[{timestamp}] User: {request.user.email if request.user.is_authenticated else 'Anonymous'}\n")
            f.write(f"[{timestamp}] GetUser: {purchaser.email if purchaser else 'None'}\n")
            f.write(f"[{timestamp}] Attendee User: {attendee_user.email}\n")
            f.write(f"[{timestamp}] Cookies: {request.COOKIES.keys()}\n")
            f.write(f"[{timestamp}] Is For Self: {is_for_self}\n")
            f.write(f"[{timestamp}] Email: {email}\n")
        
        # Create registration
        registration = None
        registration_numbers = []
        total_amount = Decimal('0')
        is_notified_later = False

        # Check if event has any active ticket types
        has_event_tickets = TicketType.objects.filter(event=event, is_active=True).exists()

        if not tickets:
            # Check if we should waitlist or confirm
            status_to_set = 'confirmed'
            if not has_event_tickets:
                status_to_set = 'waitlisted'
                is_notified_later = True

            # Free registration or waitlist
            reg = Registration.objects.create(
                event=event,
                user=attendee_user,
                purchaser=purchaser,
                attendee_name=full_name,
                attendee_email=email,
                attendee_phone=phone,
                special_requests=special_requests,
                total_amount=0,
                status=status_to_set
            )
            registration = reg
            registration_numbers.append(reg.registration_number)
        else:
            # Paid registration
            for ticket_data in tickets:
                ticket_id = ticket_data.get('ticket_id')
                quantity = int(ticket_data.get('quantity', 1))

                try:
                    ticket_type = TicketType.objects.get(id=ticket_id, event=event, is_active=True)
                except TicketType.DoesNotExist:
                    return HttpResponse(f'Ticket type {ticket_id} not found', status=404)

                # Check availability
                if not ticket_type.can_purchase(quantity):
                    return HttpResponse(f'Not enough tickets available for "{ticket_type.name}". Only {ticket_type.remaining_tickets} left.', status=400)

                # Use Decimal for currency
                ticket_price = ticket_type.price if ticket_type.price else Decimal('0')
                ticket_total = ticket_price * quantity
                total_amount += ticket_total

                reg = Registration.objects.create(
                    event=event,
                    user=attendee_user,
                    purchaser=purchaser,
                    ticket_type=ticket_type,
                    attendee_name=full_name,
                    attendee_email=email,
                    attendee_phone=phone,
                    special_requests=special_requests,
                    total_amount=ticket_total,
                    status='confirmed' if ticket_price == 0 else 'pending'
                )
                registration_numbers.append(reg.registration_number)
                
                # Atomic update to prevent overselling
                from django.db.models import F
                TicketType.objects.filter(id=ticket_id).update(quantity_sold=F('quantity_sold') + quantity)
                ticket_type.refresh_from_db()

                if registration is None:
                    registration = reg

        if not registration_numbers:
            return HttpResponse('No tickets available', status=400)

        # Send notifications
        try:
            if is_notified_later:
                from registration.models import AttendeeNotification
                AttendeeNotification.objects.create(
                    user=attendee_user,
                    notification_type='event_update',
                    title=f"Registration Received: {event.title}",
                    message=f"Thank you for registering for {event.title}. We will notify you as soon as tickets become available.",
                    related_event=event
                )
                from registration.views_success import send_no_ticket_notification
                send_no_ticket_notification(registration)
            else:
                from registration.views_success import send_qr_email_direct
                send_qr_email_direct(registration)
        except Exception as e:
            with open(log_file, 'a') as f:
                f.write(f'[{timestamp}] NOTIFICATION ERROR: {str(e)}\n')

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

    return HttpResponse('Method not allowed', status=405)
