"""
Gate Staff Portal Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from events.models import Event
from registration.models import Registration, CheckIn, RegistrationStatus
from .decorators import staff_required


@staff_required
def event_list(request):
    """
    Display list of events for staff member
    """
    # Show all events that have registrations (past, present, and future)
    # This ensures staff can check in attendees for any event
    if request.user.role in ['admin', 'organizer']:
        # For ADMIN and ORGANIZER, show all events with registrations
        events = Event.objects.filter(
            registrations__isnull=False
        ).distinct().order_by('-start_date')
    else:
        # For STAFF, show all events with registrations
        # TODO: Implement event team assignment filtering
        events = Event.objects.filter(
            registrations__isnull=False
        ).distinct().order_by('-start_date')
    
    # Add registration stats to each event
    events_with_stats = []
    for event in events:
        total_registered = Registration.objects.filter(
            event=event,
            status=RegistrationStatus.CONFIRMED
        ).count()
        total_checked_in = Registration.objects.filter(
            event=event,
            status=RegistrationStatus.CHECKED_IN
        ).count()
        
        events_with_stats.append({
            'event': event,
            'total_registered': total_registered,
            'total_checked_in': total_checked_in,
            'check_in_rate': (total_checked_in / total_registered * 100) if total_registered > 0 else 0
        })
    
    context = {
        'events': events_with_stats,
        'staff_user': request.user,
    }
    return render(request, 'staff/event_list.html', context)


@staff_required
def event_dashboard(request, event_id):
    """
    Main dashboard for a specific event with QR scanner and attendee list
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Get all confirmed registrations
    registrations = Registration.objects.filter(
        event=event,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('ticket_type').order_by('attendee_name')
    
    # Calculate stats
    total_registered = registrations.filter(status=RegistrationStatus.CONFIRMED).count()
    total_checked_in = registrations.filter(status=RegistrationStatus.CHECKED_IN).count()
    check_in_rate = (total_checked_in / (total_registered + total_checked_in) * 100) if (total_registered + total_checked_in) > 0 else 0
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        registrations = registrations.filter(
            Q(attendee_name__icontains=search_query) |
            Q(attendee_email__icontains=search_query) |
            Q(registration_number__icontains=search_query)
        )
    
    context = {
        'event': event,
        'registrations': registrations,
        'total_registered': total_registered,
        'total_checked_in': total_checked_in,
        'check_in_rate': check_in_rate,
        'search_query': search_query,
        'staff_user': request.user,
    }
    return render(request, 'staff/event_dashboard.html', context)


@staff_required
def manual_checkin(request, registration_id):
    """
    Perform manual check-in for a registration
    """
    registration = get_object_or_404(Registration, id=registration_id)
    
    if request.method == 'POST':
        if registration.status == RegistrationStatus.CHECKED_IN:
            return JsonResponse({
                'success': False,
                'message': 'Already checked in',
                'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None
            })
        
        # Perform check-in
        success = registration.check_in(checked_by=request.user)
        
        if success:
            # Log check-in
            CheckIn.objects.create(
                registration=registration,
                checked_in_by=request.user,
                method='manual',
                notes=f'Manual check-in by {request.user.email}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Check-in successful',
                'checked_in_at': registration.checked_in_at.isoformat(),
                'attendee_name': registration.attendee_name
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Check-in failed. Registration must be confirmed.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@staff_required
def qr_checkin(request, event_id):
    """
    Handle QR code check-in via staff portal
    """
    from django.http import JsonResponse
    from registration.models import CheckIn, RegistrationStatus
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    qr_code = request.POST.get('qr_code', '').strip()
    if not qr_code:
        return JsonResponse({'success': False, 'message': 'QR code is required'})
    
    event = get_object_or_404(Event, id=event_id)
    
    # Find registration by QR code
    try:
        registration = Registration.objects.get(
            qr_code=qr_code,
            event=event
        )
    except Registration.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid QR code or registration not found'})
    
    # Check if already checked in
    if registration.status == RegistrationStatus.CHECKED_IN:
        return JsonResponse({
            'success': False,
            'message': f'{registration.attendee_name} is already checked in',
            'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None
        })
    
    # Check if registration is confirmed
    if registration.status != RegistrationStatus.CONFIRMED:
        return JsonResponse({
            'success': False,
            'message': f'Registration status is {registration.get_status_display()}. Only confirmed registrations can be checked in.'
        })
    
    # Perform check-in
    success = registration.check_in(checked_by=request.user)
    
    if success:
        # Log check-in
        CheckIn.objects.create(
            registration=registration,
            checked_in_by=request.user,
            method='qr_scan',
            notes='QR code scan via staff portal'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{registration.attendee_name} checked in successfully',
            'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None,
            'registration': {
                'id': registration.id,
                'attendee_name': registration.attendee_name,
                'status': registration.status
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Check-in failed. Registration must be confirmed.'
        })


@staff_required
def checkin_stats(request, event_id):
    """
    Get real-time check-in statistics for an event
    """
    event = get_object_or_404(Event, id=event_id)
    
    total_registered = Registration.objects.filter(
        event=event,
        status=RegistrationStatus.CONFIRMED
    ).count()
    
    total_checked_in = Registration.objects.filter(
        event=event,
        status=RegistrationStatus.CHECKED_IN
    ).count()
    
    # Recent check-ins (last 10)
    recent_checkins = CheckIn.objects.filter(
        registration__event=event
    ).select_related('registration').order_by('-check_in_time')[:10]
    
    recent_checkins_data = [{
        'attendee_name': checkin.registration.attendee_name,
        'check_in_time': checkin.check_in_time.isoformat(),
        'method': checkin.method
    } for checkin in recent_checkins]
    
    return JsonResponse({
        'total_registered': total_registered,
        'total_checked_in': total_checked_in,
        'check_in_rate': (total_checked_in / (total_registered + total_checked_in) * 100) if (total_registered + total_checked_in) > 0 else 0,
        'recent_checkins': recent_checkins_data
    })
