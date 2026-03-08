#!/usr/bin/env python
import os
import django
from django.db import models

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from registration.models import Registration
from organizers.models import EventAnalytics
from events.models import Event

print("Updating analytics for all events...")

for event in Event.objects.all():
    print(f"\nEvent: {event.title}")
    
    # Get registrations for this event
    regs = Registration.objects.filter(event=event)
    total_registrations = regs.count()
    confirmed_regs = regs.filter(status='confirmed').count()
    total_revenue = regs.aggregate(total=models.Sum('total_amount'))['total'] or 0
    
    print(f"  Total registrations: {total_registrations}")
    print(f"  Confirmed registrations: {confirmed_regs}")
    print(f"  Total revenue: ${total_revenue}")
    
    # Update or create analytics
    analytics, created = EventAnalytics.objects.get_or_create(event=event)
    analytics.total_registrations = total_registrations
    analytics.checked_in_count = confirmed_regs  # For now, confirmed = checked in
    analytics.total_revenue = float(total_revenue)
    analytics.save()
    
    print(f"  Analytics {'created' if created else 'updated'}")

print("\nAnalytics update complete!")
