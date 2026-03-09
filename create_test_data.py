#!/usr/bin/env python
"""Create test data for badge printing demo"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event
from registration.models import Registration, TicketType
from datetime import datetime, timedelta

User = get_user_model()

def create_test_data():
    """Create test event and registrations for badge printing demo"""
    
    # Get admin user
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("No admin user found")
        return
    
    # Create test event if doesn't exist
    event, created = Event.objects.get_or_create(
        title="Badge Printing Demo Event",
        defaults={
            'organizer': admin_user,
            'description': 'Test event for demonstrating bulk badge printing functionality',
            'start_date': datetime.now() + timedelta(days=7),
            'end_date': datetime.now() + timedelta(days=8),
            'venue_name': 'Demo Venue',
            'address': '123 Demo Street',
            'status': 'published',
        }
    )
    
    if created:
        print(f"Created test event: {event.title}")
    else:
        print(f"Using existing event: {event.title}")
    
    # Create VIP ticket type
    vip_ticket, created = TicketType.objects.get_or_create(
        event=event,
        name='VIP Ticket',
        defaults={
            'description': 'VIP Access with all benefits',
            'ticket_category': 'vip',
            'price': 199.99,
            'quantity_available': 100,
            'sales_start': datetime.now() - timedelta(days=1),
            'sales_end': datetime.now() + timedelta(days=6),
            'benefits': 'Priority seating, Free lunch, VIP networking',
        }
    )
    
    if created:
        print(f"Created VIP ticket: {vip_ticket.name}")
    
    # Create standard ticket type
    std_ticket, created = TicketType.objects.get_or_create(
        event=event,
        name='Standard Ticket',
        defaults={
            'description': 'Standard Access',
            'ticket_category': 'standard',
            'price': 49.99,
            'quantity_available': 200,
            'sales_start': datetime.now() - timedelta(days=1),
            'sales_end': datetime.now() + timedelta(days=6),
            'benefits': 'General admission, Coffee break',
        }
    )
    
    if created:
        print(f"Created Standard ticket: {std_ticket.name}")
    
    # Create test registrations
    test_attendees = [
        {'name': 'John Smith', 'email': 'john@example.com', 'ticket': vip_ticket},
        {'name': 'Jane Doe', 'email': 'jane@example.com', 'ticket': std_ticket},
        {'name': 'Bob Johnson', 'email': 'bob@example.com', 'ticket': std_ticket},
        {'name': 'Alice Brown', 'email': 'alice@example.com', 'ticket': vip_ticket},
        {'name': 'Charlie Wilson', 'email': 'charlie@example.com', 'ticket': std_ticket},
    ]
    
    created_count = 0
    for i, attendee in enumerate(test_attendees):
        registration, created = Registration.objects.get_or_create(
            event=event,
            attendee_email=attendee['email'],
            defaults={
                'attendee_name': attendee['name'],
                'ticket_type': attendee['ticket'],
                'status': 'confirmed',
                'total_amount': attendee['ticket'].price,
                'registration_number': f'DEMO-{event.id}-{1000 + i}',
            }
        )
        
        if created:
            created_count += 1
            # Add custom fields for title and company
            registration.custom_fields = {
                'title': ['CEO', 'CTO', 'Developer', 'Designer', 'Manager'][i],
                'company': ['Tech Corp', 'Innovation Inc', 'Code Solutions', 'Creative Studio', 'Business Co'][i]
            }
            registration.save()
            print(f"Created registration for {attendee['name']}")
    
    print(f"\nTest data created successfully!")
    print(f"Event: {event.title}")
    print(f"Registrations: {created_count}")
    print(f"VIP Tickets: {Registration.objects.filter(event=event, ticket_type=vip_ticket).count()}")
    print(f"Standard Tickets: {Registration.objects.filter(event=event, ticket_type=std_ticket).count()}")
    
    print(f"\nAccess URLs:")
    print(f"Organizer Portal: http://localhost:8000")
    print(f"Attendee Portal: http://localhost:8001")
    print(f"Badge Printing: http://localhost:8000/registration/badges/{event.id}/print/")
    print(f"Admin Security: http://localhost:8000/admin/security/")

if __name__ == "__main__":
    create_test_data()
