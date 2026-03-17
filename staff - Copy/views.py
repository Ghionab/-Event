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
from advanced.models import UsherAssignment, TeamMember, TeamRole
from .decorators import staff_required
from django.contrib.auth import logout as django_logout


@staff_required
def event_list(request):
    """
    Display list of events for staff member
    """
    user = request.user

    if user.role == 'usher':
        return redirect('staff:usher_validation')

    # Get user's assigned venues if they are an usher
    assigned_venues = []
    if user.role == 'usher':
        usher_assignments = UsherAssignment.objects.filter(
            user=user,
            is_active=True
        )
        assigned_venues = list(
            usher_assignments.values_list('venue_name', flat=True)
        )
        assigned_events = Event.objects.filter(
            usher_assignments__user=user,
            usher_assignments__is_active=True
        ).distinct()
    else:
        assigned_events = None

    # Coordinator scoping: if this staff user is an assigned coordinator with
    # registration permissions, restrict visible events to their assignments.
    coordinator_events = Event.objects.none()
    if user.role == 'staff':
        coordinator_events = Event.objects.filter(
            team_members__user=user,
            team_members__is_active=True,
            team_members__role=TeamRole.COORDINATOR,
            team_members__can_manage_registrations=True,
        ).distinct()

    # Show events based on role and assignments
    if user.role in ['admin', 'organizer']:
        events_qs = Event.objects.filter(registrations__isnull=False).distinct()
    elif assigned_events is not None:
        # Usher - only show assigned events
        events_qs = assigned_events
    elif coordinator_events.exists():
        # Coordinator with explicit assignments - only those events
        events_qs = coordinator_events.filter(registrations__isnull=False).distinct()
    else:
        # Regular staff - show all events with registrations
        events_qs = Event.objects.filter(registrations__isnull=False).distinct()

    events = events_qs.order_by('-start_date')
    
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
        'staff_user': user,
        'assigned_venues': assigned_venues,
    }
    return render(request, 'staff/event_list.html', context)


@staff_required
def event_dashboard(request, event_id):
    """
    Main dashboard for a specific event with QR scanner and attendee list
    """
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # Privacy: ensure ushers and coordinators only access events they are assigned to
    if user.role == 'usher':
        if not UsherAssignment.objects.filter(user=user, event=event, is_active=True).exists():
            return redirect('staff:event_list')

    if user.role == 'staff':
        coordinator_events = Event.objects.filter(
            team_members__user=user,
            team_members__is_active=True,
            team_members__role=TeamRole.COORDINATOR,
            team_members__can_manage_registrations=True,
        ).distinct()
        if coordinator_events.exists() and event not in coordinator_events:
            return redirect('staff:event_list')

    # Get assigned venues for ushers (only for events they are assigned to)
    assigned_venues = []
    if user.role == 'usher':
        usher_assignments = UsherAssignment.objects.filter(
            user=user,
            event=event,
            is_active=True
        )
        assigned_venues = list(
            usher_assignments.values_list('venue_name', flat=True)
        )

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
        'staff_user': user,
        'assigned_venues': assigned_venues,
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
            location = ''
            if request.user.role == 'usher':
                assignment = UsherAssignment.objects.filter(
                    user=request.user,
                    event=registration.event,
                    is_active=True
                ).order_by('-assigned_at').first()
                location = assignment.venue_name if assignment else ''

            CheckIn.objects.create(
                registration=registration,
                checked_in_by=request.user,
                method='manual',
                location=location,
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
        location = ''
        if request.user.role == 'usher':
            assignment = UsherAssignment.objects.filter(
                user=request.user,
                event=event,
                is_active=True
            ).order_by('-assigned_at').first()
            location = assignment.venue_name if assignment else ''

        CheckIn.objects.create(
            registration=registration,
            checked_in_by=request.user,
            method='qr_scan',
            location=location,
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


@staff_required
def usher_validation(request):
    """Usher-only ticket validation page (no event selection)."""
    if request.user.role != 'usher':
        return redirect('staff:event_list')

    assignment = UsherAssignment.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('event').order_by('-assigned_at').first()

    if not assignment:
        return render(request, 'staff/usher_validation.html', {
            'assignment': None,
        })

    return render(request, 'staff/usher_validation.html', {
        'assignment': assignment,
    })


@staff_required
def usher_manual_checkin(request):
    """Check-in by registration number for ushers (scoped to active assignment event)."""
    if request.user.role != 'usher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    ticket_id = request.POST.get('ticket_id', '').strip().upper()
    if not ticket_id:
        return JsonResponse({'success': False, 'message': 'Ticket ID is required'})

    assignment = UsherAssignment.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('event').order_by('-assigned_at').first()

    if not assignment:
        return JsonResponse({'success': False, 'message': 'No active usher assignment found'})

    try:
        registration = Registration.objects.get(
            registration_number=ticket_id,
            event=assignment.event,
        )
    except Registration.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Ticket not found for your assigned event'})

    if registration.status == RegistrationStatus.CHECKED_IN:
        return JsonResponse({
            'success': False,
            'message': f'{registration.attendee_name} is already checked in',
            'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None
        })

    if registration.status != RegistrationStatus.CONFIRMED:
        return JsonResponse({
            'success': False,
            'message': f'Registration status is {registration.get_status_display()}. Only confirmed registrations can be checked in.'
        })

    success = registration.check_in(checked_by=request.user)
    if not success:
        return JsonResponse({'success': False, 'message': 'Check-in failed. Registration must be confirmed.'})

    CheckIn.objects.create(
        registration=registration,
        checked_in_by=request.user,
        method='manual',
        location=assignment.venue_name,
        notes='Manual ticket ID entry via usher validation'
    )

    return JsonResponse({
        'success': True,
        'message': f'{registration.attendee_name} checked in successfully',
        'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None,
        'registration': {
            'id': registration.id,
            'attendee_name': registration.attendee_name,
            'status': registration.status,
            'registration_number': registration.registration_number,
        }
    })


@staff_required
def usher_qr_checkin(request):
    """Check-in by QR code for ushers (scoped to active assignment event)."""
    if request.user.role != 'usher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    qr_code = request.POST.get('qr_code', '').strip()
    if not qr_code:
        return JsonResponse({'success': False, 'message': 'QR code is required'})

    assignment = UsherAssignment.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('event').order_by('-assigned_at').first()

    if not assignment:
        return JsonResponse({'success': False, 'message': 'No active usher assignment found'})

    try:
        registration = Registration.objects.get(
            qr_code=qr_code,
            event=assignment.event,
        )
    except Registration.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid QR code or registration not found for your assigned event'})

    if registration.status == RegistrationStatus.CHECKED_IN:
        return JsonResponse({
            'success': False,
            'message': f'{registration.attendee_name} is already checked in',
            'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None
        })

    if registration.status != RegistrationStatus.CONFIRMED:
        return JsonResponse({
            'success': False,
            'message': f'Registration status is {registration.get_status_display()}. Only confirmed registrations can be checked in.'
        })

    success = registration.check_in(checked_by=request.user)
    if not success:
        return JsonResponse({'success': False, 'message': 'Check-in failed. Registration must be confirmed.'})

    CheckIn.objects.create(
        registration=registration,
        checked_in_by=request.user,
        method='qr_scan',
        location=assignment.venue_name,
        notes='QR scan via usher validation'
    )

    return JsonResponse({
        'success': True,
        'message': f'{registration.attendee_name} checked in successfully',
        'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None,
        'registration': {
            'id': registration.id,
            'attendee_name': registration.attendee_name,
            'status': registration.status,
            'registration_number': registration.registration_number,
        }
    })


@staff_required
def staff_logout(request):
    """
    Custom logout view for staff that immediately redirects to login.
    """
    django_logout(request)
    return redirect('staff_login')