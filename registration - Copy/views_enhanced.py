from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from events.models import Event
from .models import (
    TicketPurchase, Ticket, TicketAnswer, TicketType, 
    PromoCode, RegistrationField
)
from .forms_enhanced import (
    TicketPurchaseForm, AttendeeInfoForm, CustomQuestionForm
)
import json


@login_required
def enhanced_ticket_purchase(request, event_id):
    """
    Enhanced ticket purchase flow with:
    - Auto-fill user information
    - Multiple attendees support
    - Custom questions per ticket
    - Buyer vs attendee separation
    """
    event = get_object_or_404(Event, id=event_id)
    ticket_types = event.ticket_types.filter(is_active=True)
    custom_questions = event.registration_fields.filter(is_active=True).order_by('order')
    
    if request.method == 'POST':
        return handle_ticket_purchase_submission(request, event, custom_questions)
    
    # GET request - show the purchase form
    context = {
        'event': event,
        'ticket_types': ticket_types,
        'custom_questions': custom_questions,
        'user': request.user,
    }
    
    return render(request, 'registration/enhanced_purchase.html', context)


@transaction.atomic
def handle_ticket_purchase_submission(request, event, custom_questions):
    """Handle the ticket purchase form submission"""
    try:
        # Parse the submitted data
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        # Extract purchase-level data
        promo_code_value = data.get('promo_code', '').strip().upper()
        tickets_data = data.get('tickets', [])
        
        if not tickets_data:
            return JsonResponse({'error': 'No tickets selected'}, status=400)
        
        # Create the purchase
        purchase = TicketPurchase.objects.create(
            buyer=request.user,
            event=event
        )
        
        total_amount = 0
        discount_amount = 0
        
        # Process each ticket entry (always quantity = 1 now)
        for ticket_data in tickets_data:
            ticket_type_id = ticket_data.get('ticket_type_id') or ticket_data.get('ticket_id')
            attendee_name = ticket_data.get('attendee_name', '').strip()
            attendee_email = ticket_data.get('attendee_email', '').strip()
            attendee_phone = ticket_data.get('attendee_phone', '').strip()
            custom_answers = ticket_data.get('custom_answers', {})
            
            # Force quantity to 1
            quantity = 1
            
            # Validate required fields
            if not attendee_name or not attendee_email:
                purchase.delete()
                return JsonResponse({
                    'error': 'Attendee name and email are required for all tickets'
                }, status=400)
            
            # Get ticket type
            try:
                ticket_type = TicketType.objects.get(id=ticket_type_id, event=event, is_active=True)
            except TicketType.DoesNotExist:
                purchase.delete()
                return JsonResponse({'error': f'Invalid ticket type: {ticket_type_id}'}, status=400)
            
            # Check availability (always check for 1 ticket now)
            if ticket_type.remaining_tickets < 1:
                purchase.delete()
                return JsonResponse({
                    'error': f'Not enough tickets available for "{ticket_type.name}". '
                             f'Available: {ticket_type.remaining_tickets}'
                }, status=400)
            
            # Create single ticket record
            ticket = Ticket.objects.create(
                purchase=purchase,
                event=event,
                ticket_type=ticket_type,
                attendee_name=attendee_name,
                attendee_email=attendee_email,
                attendee_phone=attendee_phone,
                status='confirmed'
            )
            
            # Save custom question answers
            for question_id, answer in custom_answers.items():
                try:
                    question = custom_questions.get(id=int(question_id))
                    TicketAnswer.objects.create(
                        ticket=ticket,
                        question=question,
                        answer=str(answer)
                    )
                except (RegistrationField.DoesNotExist, ValueError):
                    continue
            
            # Update ticket sold count by 1
            from django.db.models import F
            TicketType.objects.filter(id=ticket_type.id).update(quantity_sold=F('quantity_sold') + 1)
            ticket_type.refresh_from_db()
            
            # Add to total (price * 1)
            total_amount += float(ticket_type.price or 0)
        
        # Apply promo code if provided
        if promo_code_value:
            try:
                promo = PromoCode.objects.get(
                    code=promo_code_value,
                    event=event,
                    is_active=True
                )
                if promo.is_valid():
                    discounted_total, discount = promo.apply_discount(total_amount)
                    discount_amount = discount
                    total_amount = discounted_total
                    purchase.promo_code = promo
                    promo.current_uses += 1
                    promo.save()
                else:
                    purchase.delete()
                    return JsonResponse({
                        'error': 'Promo code is expired or has reached its usage limit'
                    }, status=400)
            except PromoCode.DoesNotExist:
                purchase.delete()
                return JsonResponse({'error': 'Invalid promo code'}, status=400)
        
        # Update purchase totals
        purchase.total_amount = total_amount
        purchase.discount_amount = discount_amount
        purchase.payment_status = 'completed' if total_amount == 0 else 'pending'
        purchase.save()
        
        # Return success response
        return JsonResponse({
            'success': True,
            'purchase_number': purchase.purchase_number,
            'total_amount': float(total_amount),
            'discount_amount': float(discount_amount),
            'ticket_count': purchase.get_ticket_count(),
            'redirect_url': f'/registration/purchase-success/{purchase.id}/'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def purchase_success(request, purchase_id):
    """Display purchase success page"""
    purchase = get_object_or_404(TicketPurchase, id=purchase_id, buyer=request.user)
    tickets = purchase.tickets.all()
    
    context = {
        'purchase': purchase,
        'tickets': tickets,
    }
    
    return render(request, 'registration/purchase_success.html', context)


@login_required
def my_purchases(request):
    """List all purchases made by the logged-in user"""
    purchases = TicketPurchase.objects.filter(buyer=request.user).prefetch_related('tickets')
    
    context = {
        'purchases': purchases,
    }
    
    return render(request, 'registration/my_purchases.html', context)


@login_required
def purchase_detail(request, purchase_id):
    """View details of a specific purchase"""
    purchase = get_object_or_404(TicketPurchase, id=purchase_id, buyer=request.user)
    tickets = purchase.tickets.all().prefetch_related('answers__question')
    
    context = {
        'purchase': purchase,
        'tickets': tickets,
    }
    
    return render(request, 'registration/purchase_detail.html', context)


@require_http_methods(["GET"])
def get_user_info_api(request):
    """API endpoint to get logged-in user info for auto-fill"""
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False})
    
    user = request.user
    return JsonResponse({
        'authenticated': True,
        'name': user.get_full_name() or user.email,
        'email': user.email,
        'phone': getattr(user, 'phone', ''),
    })


@require_http_methods(["POST"])
def validate_promo_code_api(request):
    """API endpoint to validate promo code"""
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
        event_id = data.get('event_id')
        total_amount = float(data.get('total_amount', 0))
        
        if not code or not event_id:
            return JsonResponse({'valid': False, 'error': 'Missing required fields'}, status=400)
        
        event = Event.objects.get(id=event_id)
        promo = PromoCode.objects.get(code=code, event=event, is_active=True)
        
        if not promo.is_valid():
            return JsonResponse({
                'valid': False,
                'error': 'Promo code is expired or has reached its usage limit'
            })
        
        discounted_total, discount = promo.apply_discount(total_amount)
        
        return JsonResponse({
            'valid': True,
            'discount_type': promo.discount_type,
            'discount_value': float(promo.discount_value),
            'discount_amount': float(discount),
            'discounted_total': float(discounted_total),
            'original_total': float(total_amount),
        })
    
    except (Event.DoesNotExist, PromoCode.DoesNotExist):
        return JsonResponse({'valid': False, 'error': 'Invalid promo code'})
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)}, status=500)
