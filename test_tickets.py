#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_participant')
django.setup()

from registration.models import TicketType
from events.models import Event

print("Events:", Event.objects.all().count())
print("Tickets:", TicketType.objects.all().count())

event = Event.objects.first()
print(f"Event: {event.title}")
print("Event tickets:")
for ticket in event.ticket_types.all():
    print(f"  {ticket.name} - Active: {ticket.is_active} - Price: {ticket.price}")

# Test API response
print("\n--- Testing API ---")
tickets = TicketType.objects.filter(event_id=event.id, is_active=True)
print(f"Active tickets for event {event.id}: {tickets.count()}")
for ticket in tickets:
    print(f"  {ticket.name}")
