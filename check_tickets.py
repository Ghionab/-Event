#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_participant')
django.setup()

from registration.models import TicketType, Registration
from events.models import Event

print("Checking ticket data...")
event = Event.objects.first()
print(f"Event: {event.title}")

for ticket in TicketType.objects.filter(event=event):
    print(f"\nTicket: {ticket.name}")
    print(f"  Quantity Available: {ticket.quantity_available}")
    print(f"  Quantity Sold: {ticket.quantity_sold}")
    print(f"  Is Active: {ticket.is_active}")
    print(f"  Available Calculation: {ticket.available_quantity}")
    
    # Check registrations
    regs = Registration.objects.filter(ticket_type=ticket)
    print(f"  Actual Registrations: {regs.count()}")
    
    # Test available calculation
    available = ticket.quantity_available - ticket.quantity_sold
    print(f"  Should Show Available: {available}")
