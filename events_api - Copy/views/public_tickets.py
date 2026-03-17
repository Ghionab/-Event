"""
Public API for creating tickets - for testing purposes
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from events.models import Event
from registration.models import TicketType


@api_view(['POST'])
@permission_classes([AllowAny])
def public_create_ticket(request):
    """Create a ticket for an event (public endpoint for testing)"""
    event_id = request.data.get('event_id')
    name = request.data.get('name', 'General Admission')
    price = float(request.data.get('price', 0))
    quantity = int(request.data.get('quantity', 100))
    ticket_category = request.data.get('ticket_category', 'regular')

    if not event_id:
        return Response({'error': 'Event ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        event = Event.objects.get(id=event_id, organizer=request.user) if request.user.is_authenticated else Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

    ticket = TicketType.objects.create(
        event=event,
        name=name,
        ticket_category=ticket_category,
        price=price,
        quantity_available=quantity,
        quantity_sold=0,
        sales_start=event.start_date,
        sales_end=event.end_date,
        is_active=True
    )

    return Response({
        'id': ticket.id,
        'name': ticket.name,
        'price': float(ticket.price),
        'quantity_available': ticket.quantity_available,
        'message': 'Ticket created successfully!'
    })
