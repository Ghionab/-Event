#!/usr/bin/env python
"""
Command-line interface for Coordinator Portal
"""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_coordinator')
django.setup()

from django.contrib.auth.models import User
from events.models import Event, EventSession
from registration.models import Registration
from datetime import datetime

def show_menu():
    print("\n" + "="*50)
    print("COORDINATOR PORTAL - COMMAND LINE INTERFACE")
    print("="*50)
    print("1. View All Events")
    print("2. View Event Details")
    print("3. View Registrations")
    print("4. View Registration Statistics")
    print("5. Check-in Attendee")
    print("6. Exit")
    print("="*50)

def view_events():
    print("\n--- ALL EVENTS ---")
    events = Event.objects.all()
    if not events:
        print("No events found.")
        return
    
    for event in events:
        print(f"ID: {event.id} | {event.title}")
        print(f"   Date: {event.start_date} - {event.end_date}")
        print(f"   Location: {event.location}")
        print(f"   Status: {event.status}")
        print("-" * 40)

def view_event_details():
    try:
        event_id = input("Enter Event ID: ")
        event = Event.objects.get(id=event_id)
        
        print(f"\n--- EVENT DETAILS: {event.title} ---")
        print(f"Description: {event.description}")
        print(f"Start Date: {event.start_date}")
        print(f"End Date: {event.end_date}")
        print(f"Location: {event.location}")
        print(f"Status: {event.status}")
        print(f"Max Attendees: {event.max_attendees}")
        print(f"Current Registrations: {event.registrations.count()}")
        
        sessions = EventSession.objects.filter(event=event)
        if sessions:
            print("\nSessions:")
            for session in sessions:
                print(f"  - {session.title} ({session.start_time} - {session.end_time})")
        
    except Event.DoesNotExist:
        print("Event not found!")
    except ValueError:
        print("Invalid Event ID!")

def view_registrations():
    print("\n--- REGISTRATIONS ---")
    registrations = Registration.objects.all().order_by('-registration_date')[:20]
    
    if not registrations:
        print("No registrations found.")
        return
    
    for reg in registrations:
        print(f"ID: {reg.id} | {reg.attendee_name} ({reg.email})")
        print(f"   Event: {reg.event.title}")
        print(f"   Status: {reg.status}")
        print(f"   Date: {reg.registration_date}")
        print("-" * 40)

def view_statistics():
    print("\n--- REGISTRATION STATISTICS ---")
    
    total_events = Event.objects.count()
    total_registrations = Registration.objects.count()
    pending_registrations = Registration.objects.filter(status='pending').count()
    confirmed_registrations = Registration.objects.filter(status='confirmed').count()
    
    print(f"Total Events: {total_events}")
    print(f"Total Registrations: {total_registrations}")
    print(f"Pending Registrations: {pending_registrations}")
    print(f"Confirmed Registrations: {confirmed_registrations}")
    
    # Event-wise statistics
    print("\n--- Event-wise Statistics ---")
    events = Event.objects.all()
    for event in events:
        reg_count = Registration.objects.filter(event=event).count()
        print(f"{event.title}: {reg_count} registrations")

def check_in_attendee():
    print("\n--- CHECK-IN ATTENDEE ---")
    try:
        registration_id = input("Enter Registration ID: ")
        registration = Registration.objects.get(id=registration_id)
        
        if registration.status == 'confirmed':
            registration.status = 'checked_in'
            registration.check_in_time = datetime.now()
            registration.save()
            print(f"✓ Successfully checked in: {registration.attendee_name}")
        else:
            print(f"Cannot check in. Current status: {registration.status}")
            
    except Registration.DoesNotExist:
        print("Registration not found!")
    except ValueError:
        print("Invalid Registration ID!")

def main():
    print("Starting Coordinator Portal CLI...")
    
    while True:
        show_menu()
        choice = input("Enter your choice (1-6): ")
        
        if choice == '1':
            view_events()
        elif choice == '2':
            view_event_details()
        elif choice == '3':
            view_registrations()
        elif choice == '4':
            view_statistics()
        elif choice == '5':
            check_in_attendee()
        elif choice == '6':
            print("Exiting Coordinator Portal CLI...")
            break
        else:
            print("Invalid choice! Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()
