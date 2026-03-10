from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from decimal import Decimal

from .models import (
    OrganizerProfile, OrganizerTeamMember, EventAnalytics,
    EventTemplate, OrganizerNotification, OrganizerPayout
)
from events.models import Event, EventSession, Sponsor
from registration.models import Registration, TicketType, CheckIn
from communication.models import EmailTemplate, EmailLog, ScheduledEmail, LivePoll, LiveQA
from communication.forms import EmailTemplateForm, ScheduledEmailForm, LivePollForm
from events.forms import SponsorForm

from .forms import RegistrationEditForm

def organizer_required(view_func):
    """Decorator to ensure user has organizer profile"""
    import functools
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            organizer = OrganizerProfile.objects.get(user=request.user)
            request.organizer = organizer
            return view_func(request, *args, **kwargs)
        except OrganizerProfile.DoesNotExist:
            messages.error(request, 'You need to create an organizer profile first.')
            return redirect('organizer_create')
    return wrapper


@login_required
@organizer_required
def dashboard(request):
    """Organizer dashboard with overview of all events"""
    organizer = request.organizer
    
    # Get all events organized by this user
    events = Event.objects.filter(organizer=organizer.user)
    
    # Stats
    total_events = events.count()
    published_events = events.filter(status='published').count()
    upcoming_events = events.filter(start_date__gte=timezone.now()).count()
    
    # Registration stats
    total_registrations = Registration.objects.filter(event__in=events).count()
    total_revenue = Registration.objects.filter(
        event__in=events, status='confirmed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent registrations
    recent_registrations = Registration.objects.filter(
        event__in=events
    ).order_by('-created_at')[:10]
    
    # Recent notifications
    notifications = OrganizerNotification.objects.filter(
        organizer=organizer
    )[:5]
    
    context = {
        'organizer': organizer,
        'events': events[:5],
        'total_events': total_events,
        'published_events': published_events,
        'upcoming_events': upcoming_events,
        'total_registrations': total_registrations,
        'total_revenue': total_revenue,
        'recent_registrations': recent_registrations,
        'notifications': notifications,
    }
    return render(request, 'organizers/dashboard.html', context)


@login_required
def organizer_create(request):
    """Create organizer profile"""
    from .forms import OrganizerProfileForm
    from users.models import UserRole
    
    
    if request.method == 'POST':
        form = OrganizerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Organizer profile created successfully!')
            return redirect('organizer_dashboard')
    else:
        form = OrganizerProfileForm()
    
    return render(request, 'organizers/organizer_form.html', {'form': form, 'title': 'Create Organizer Profile'})


@login_required
@organizer_required
def event_list(request):
    """List all events for the organizer"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user).order_by('-created_at')
    
    return render(request, 'organizers/event_list.html', {
        'events': events,
        'organizer': organizer
    })


@login_required
@organizer_required
def event_create(request):
    """Create a new event"""
    from events.forms import EventForm
    templates = EventTemplate.objects.filter(organizer=request.organizer)

    initial = {}
    selected_template_id = request.GET.get('template') or request.POST.get('template')
    selected_template = None
    if selected_template_id:
        try:
            selected_template = templates.get(id=selected_template_id)
            # Pre-fill initial data from template
            initial = {
                'title': selected_template.name,
                'description': selected_template.description,
                'event_type': selected_template.event_type,
                'primary_color': selected_template.default_primary_color,
                'secondary_color': selected_template.default_secondary_color,
            }
        except EventTemplate.DoesNotExist:
            pass

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, initial=initial)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.status = 'published'  # Auto-publish on creation
            event.save()
            messages.success(request, 'Event created and published successfully!')
            # Redirect to event setup wizard
            return redirect('organizer_event_setup', event_id=event.id)
    else:
        form = EventForm(initial=initial)

    return render(request, 'organizers/event_form.html', {
        'form': form,
        'title': 'Create Event',
        'templates': templates,
        'selected_template_id': int(selected_template_id) if selected_template_id else None,
    })


@login_required
@organizer_required
def event_setup(request, event_id):
    """Event setup wizard - tickets, team, invitations"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    # Get event data
    tickets = TicketType.objects.filter(event=event)
    team_members = OrganizerTeamMember.objects.filter(organizer=request.organizer, is_active=True)

    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_ticket':
            from registration.forms import TicketTypeForm
            form = TicketTypeForm(request.POST)
            if form.is_valid():
                ticket = form.save(commit=False)
                ticket.event = event
                ticket.save()
                messages.success(request, 'Ticket added successfully!')
            return redirect('organizer_event_setup', event_id=event.id)

        elif action == 'delete_ticket':
            ticket_id = request.POST.get('ticket_id')
            ticket = get_object_or_404(TicketType, id=ticket_id, event=event)
            ticket.delete()
            messages.success(request, 'Ticket deleted successfully!')
            return redirect('organizer_event_setup', event_id=event.id)

        elif action == 'send_invitations':
            emails = request.POST.get('emails', '')
            phone_numbers = request.POST.get('phone_numbers', '')
            message = request.POST.get('message', '')

            # Process emails
            email_list = [e.strip() for e in emails.split(',') if e.strip()]

            # Save invitation message to event (if you have a field for it)
            # For now, we'll just show success
            if email_list or phone_numbers:
                # Create notification for sent invitations
                OrganizerNotification.objects.create(
                    organizer=request.organizer,
                    title='Invitations Sent',
                    message=f'Invitations sent to {len(email_list)} email(s)',
                    notification_type='update'
                )
                messages.success(request, f'Invitations sent to {len(email_list)} recipient(s)!')
            else:
                messages.warning(request, 'Please add at least one email or phone number.')
            return redirect('organizer_event_setup', event_id=event.id)

        elif action == 'import_team_csv':
            import csv
            import io
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            csv_file = request.FILES.get('team_csv')
            
            if not csv_file:
                messages.error(request, 'Please select a CSV file to upload.')
                return redirect('organizer_event_setup', event_id=event.id)
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('organizer_event_setup', event_id=event.id)
            
            try:
                # Read CSV file
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                imported_count = 0
                error_count = 0
                errors = []
                
                for row in reader:
                    try:
                        # Get required fields
                        name = row.get('name', '').strip()
                        email = row.get('email', '').strip()
                        role = row.get('role', 'Team Member').strip()
                        
                        if not email:
                            error_count += 1
                            errors.append(f"Row {reader.line_num}: Missing email")
                            continue
                        
                        # Validate email format
                        from django.core.validators import validate_email
                        from django.core.exceptions import ValidationError
                        try:
                            validate_email(email)
                        except ValidationError:
                            error_count += 1
                            errors.append(f"Row {reader.line_num}: Invalid email - {email}")
                            continue
                        
                        # Check if user already exists
                        user = User.objects.filter(email=email).first()
                        
                        if not user:
                            # Create new user - use email as identifier since username field doesn't exist
                            import secrets
                            temp_password = secrets.token_urlsafe(12)
                            
                            # Get the USERNAME_FIELD from User model to determine what to use
                            user_identifier = email  # Use email as the identifier
                            
                            user = User.objects.create_user(
                                email=user_identifier,
                                password=temp_password,
                                first_name=name.split()[0] if name else '',
                                last_name=' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
                            )
                            
                            # TODO: Send invitation email with password reset link
                        
                        # Check if team member already exists for this organizer
                        existing_member = OrganizerTeamMember.objects.filter(
                            organizer=request.organizer,
                            user=user
                        ).first()
                        
                        if existing_member:
                            # Update role if changed
                            if existing_member.role != role:
                                existing_member.role = role
                                existing_member.save()
                        else:
                            # Create new team member
                            OrganizerTeamMember.objects.create(
                                organizer=request.organizer,
                                user=user,
                                role=role,
                                permissions={},
                                is_active=True
                            )
                        
                        # Also register the user for the event
                        from registration.models import Registration, RegistrationStatus
                        existing_registration = Registration.objects.filter(
                            event=event,
                            user=user
                        ).first()
                        
                        if not existing_registration:
                            Registration.objects.create(
                                event=event,
                                user=user,
                                attendee_name=user.get_full_name() or name or user.email,
                                attendee_email=user.email,
                                status=RegistrationStatus.CONFIRMED,
                                total_amount=0
                            )
                        
                        imported_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {reader.line_num}: {str(e)}")
                
                # Show results
                if imported_count > 0:
                    messages.success(request, f'Successfully imported {imported_count} team member(s)!')
                
                if error_count > 0:
                    messages.warning(request, f'{error_count} row(s) had errors. First few errors: {", ".join(errors[:3])}')
                
                if imported_count == 0 and error_count == 0:
                    messages.warning(request, 'No valid team members found in the CSV file.')
                    
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
            
            return redirect('organizer_event_setup', event_id=event.id)

        elif action == 'finish':
            # Mark event as ready (update status if needed)
            if event.status == 'draft':
                event.status = 'published'
                event.save()
            messages.success(request, f'Event "{event.title}" is now live!')
            return redirect('organizer_event_detail', event_id=event.id)

    context = {
        'event': event,
        'tickets': tickets,
        'team_members': team_members,
    }
    return render(request, 'organizers/event_setup.html', context)


@login_required
@organizer_required
def import_team_csv(request, event_id):
    """Dedicated view for importing team members via CSV"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    
    if request.method != 'POST':
        return redirect('organizer_event_setup', event_id=event.id)
    
    import csv
    import io
    from django.contrib.auth import get_user_model
    from registration.models import Registration, RegistrationStatus
    
    User = get_user_model()
    csv_file = request.FILES.get('team_csv')
    
    if not csv_file:
        messages.error(request, 'Please select a CSV file to upload.')
        return redirect('organizer_event_setup', event_id=event.id)
    
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'Please upload a valid CSV file.')
        return redirect('organizer_event_setup', event_id=event.id)
    
    try:
        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        imported_count = 0
        error_count = 0
        errors = []
        
        for row in reader:
            try:
                # Get required fields
                name = row.get('name', '').strip()
                email = row.get('email', '').strip()
                role = row.get('role', 'Team Member').strip()
                
                if not email:
                    error_count += 1
                    errors.append(f"Row {reader.line_num}: Missing email")
                    continue
                
                # Validate email format
                from django.core.validators import validate_email
                from django.core.exceptions import ValidationError
                try:
                    validate_email(email)
                except ValidationError:
                    error_count += 1
                    errors.append(f"Row {reader.line_num}: Invalid email - {email}")
                    continue
                
                # Check if user already exists
                user = User.objects.filter(email=email).first()
                
                if not user:
                    # Create new user - use email as identifier
                    import secrets
                    temp_password = secrets.token_urlsafe(12)
                    
                    user = User.objects.create_user(
                        email=email,
                        password=temp_password,
                        first_name=name.split()[0] if name else '',
                        last_name=' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
                    )
                
                # Check if team member already exists for this organizer
                existing_member = OrganizerTeamMember.objects.filter(
                    organizer=request.organizer,
                    user=user
                ).first()
                
                if existing_member:
                    # Update role if changed
                    if existing_member.role != role:
                        existing_member.role = role
                        existing_member.save()
                else:
                    # Create new team member
                    OrganizerTeamMember.objects.create(
                        organizer=request.organizer,
                        user=user,
                        role=role,
                        permissions={},
                        is_active=True
                    )
                
                # Also register the user for the event
                existing_registration = Registration.objects.filter(
                    event=event,
                    user=user
                ).first()
                
                if not existing_registration:
                    Registration.objects.create(
                        event=event,
                        user=user,
                        attendee_name=user.get_full_name() or name or user.email,
                        attendee_email=user.email,
                        status=RegistrationStatus.CONFIRMED,
                        total_amount=0
                    )
                
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {reader.line_num}: {str(e)}")
        
        # Show results
        if imported_count > 0:
            messages.success(request, f'Successfully imported {imported_count} team member(s) and registered them for the event!')
        
        if error_count > 0:
            messages.warning(request, f'{error_count} row(s) had errors. First few errors: {", ".join(errors[:3])}')
        
        if imported_count == 0 and error_count == 0:
            messages.warning(request, 'No valid team members found in the CSV file.')
            
    except Exception as e:
        messages.error(request, f'Error processing CSV file: {str(e)}')
    
    return redirect('organizer_event_setup', event_id=event.id)


@login_required
@organizer_required
def event_detail(request, event_id):
    """View event details and analytics"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    # Get or create analytics
    analytics, created = EventAnalytics.objects.get_or_create(event=event)

    # Registrations
    registrations = Registration.objects.filter(event=event).order_by('-created_at')

    # Ticket types
    ticket_types = TicketType.objects.filter(event=event)

    # Calculate ticket sales with actual amounts from registrations
    ticket_sales = []
    total_tickets_sold = 0
    total_revenue = 0

    for ticket in ticket_types:
        # Get registrations for this ticket type
        ticket_regs = registrations.filter(ticket_type=ticket)
        sold_count = ticket_regs.count()
        # Sum actual revenue from registrations
        revenue = ticket_regs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_tickets_sold += sold_count
        total_revenue += float(revenue)
        ticket_sales.append({
            'name': ticket.name,
            'sold': sold_count,
            'price': ticket.price,
            'revenue': float(revenue),
        })

    # Total registrations
    total_registrations = registrations.count()

    context = {
        'event': event,
        'analytics': analytics,
        'registrations': registrations[:20],
        'ticket_types': ticket_types,
        'ticket_sales': ticket_sales,
        'total_tickets_sold': total_tickets_sold,
        'total_revenue': total_revenue,
        'total_registrations': total_registrations,
    }
    return render(request, 'organizers/event_detail.html', context)


@login_required
@organizer_required
def event_edit(request, event_id):
    """Edit an existing event"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    from events.forms import EventForm

    # Handle ticket actions
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_ticket':
            from registration.forms import TicketTypeForm
            ticket_form = TicketTypeForm(request.POST)
            if ticket_form.is_valid():
                ticket = ticket_form.save(commit=False)
                ticket.event = event
                ticket.save()
                messages.success(request, 'Ticket added successfully!')
            return redirect('organizer_event_edit', event_id=event.id)

        elif action == 'edit_ticket':
            ticket_id = request.POST.get('ticket_id')
            ticket = get_object_or_404(TicketType, id=ticket_id, event=event)
            from registration.forms import TicketTypeForm
            ticket_form = TicketTypeForm(request.POST, instance=ticket)
            if ticket_form.is_valid():
                ticket_form.save()
                messages.success(request, 'Ticket updated successfully!')
            return redirect('organizer_event_edit', event_id=event.id)

        elif action == 'delete_ticket':
            ticket_id = request.POST.get('ticket_id')
            ticket = get_object_or_404(TicketType, id=ticket_id, event=event)
            ticket.delete()
            messages.success(request, 'Ticket deleted successfully!')
            return redirect('organizer_event_edit', event_id=event.id)

        elif action == 'save_event':
            form = EventForm(request.POST, request.FILES, instance=event)
            if form.is_valid():
                form.save()
                messages.success(request, 'Event updated successfully!')
                return redirect('organizer_event_detail', event_id=event.id)

    # Get existing tickets
    tickets = TicketType.objects.filter(event=event)

    # Get ticket form for adding new tickets
    from registration.forms import TicketTypeForm
    ticket_form = TicketTypeForm()

    form = EventForm(instance=event)

    return render(request, 'organizers/event_edit.html', {
        'form': form,
        'title': 'Edit Event',
        'event': event,
        'tickets': tickets,
        'ticket_form': ticket_form
    })


@login_required
@organizer_required
def event_delete(request, event_id):
    """Delete an event"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('organizer_event_list')
    
    return render(request, 'organizers/event_confirm_delete.html', {'event': event})


@login_required
@organizer_required
def analytics(request, event_id=None):
    """View analytics for events"""
    organizer = request.organizer
    
    if event_id:
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        analytics = get_object_or_404(EventAnalytics, event=event)
        return render(request, 'organizers/analytics_detail.html', {
            'event': event,
            'analytics': analytics
        })
    
    # Overall analytics
    events = Event.objects.filter(organizer=organizer.user)
    
    # Registration trends - calculate from actual Registration data
    registrations_qs = Registration.objects.filter(
        event__in=events, status__in=['confirmed', 'checked_in']
    )
    
    # Calculate summary statistics from actual data
    total_registrations = registrations_qs.count()
    total_revenue = registrations_qs.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    checked_in = Registration.objects.filter(
        event__in=events, status='checked_in'
    ).count()
    
    # Calculate total views from EventAnalytics (this is tracked separately)
    total_views = EventAnalytics.objects.filter(
        event__in=events
    ).aggregate(total=Sum('total_views'))['total'] or 0
    
    # Registration trends by date
    registrations = Registration.objects.filter(
        event__in=events, status__in=['confirmed', 'checked_in']
    ).annotate(date=TruncDate('created_at')).values('date').annotate(
        count=Count('id'), revenue=Sum('total_amount')
    ).order_by('date')
    
    context = {
        'events': events,
        'registrations': registrations,
        'total_views': total_views,
        'total_registrations': total_registrations,
        'checked_in': checked_in,
        'total_revenue': total_revenue,
    }
    return render(request, 'organizers/analytics.html', context)


@login_required
@organizer_required
def team_members(request):
    """Manage team members"""
    organizer = request.organizer
    team_members = OrganizerTeamMember.objects.filter(organizer=organizer)
    
    return render(request, 'organizers/team_list.html', {
        'team_members': team_members,
        'organizer': organizer
    })


@login_required
@organizer_required
def templates(request):
    """Manage event templates"""
    organizer = request.organizer
    templates = EventTemplate.objects.filter(organizer=organizer)
    
    return render(request, 'organizers/template_list.html', {
        'templates': templates,
        'organizer': organizer
    })


@login_required
@organizer_required
def template_detail(request, template_id):
    """Preview a specific event template"""
    template = get_object_or_404(EventTemplate, id=template_id, organizer=request.organizer)
    
    return render(request, 'organizers/template_detail.html', {
        'template': template,
        'title': template.name
    })


@login_required
@organizer_required
def template_create(request):
    """Create a new event template"""
    from .forms import EventTemplateForm
    
    if request.method == 'POST':
        form = EventTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.organizer = request.organizer
            template.save()
            messages.success(request, 'Template created successfully!')
            return redirect('organizer_templates')
        else:
            print("FORM ERRORS:", form.errors)
            messages.error(request, f'Form errors: {form.errors}')
    else:
        form = EventTemplateForm()
    
    return render(request, 'organizers/template_form.html', {
        'form': form,
        'title': 'Create Template'
    })


@login_required
@organizer_required
def settings(request):
    """Organizer settings"""
    organizer = request.organizer
    
    return render(request, 'organizers/settings.html', {'organizer': organizer})


@login_required
@organizer_required
def notifications(request):
    """View all notifications"""
    notifications = OrganizerNotification.objects.filter(
        organizer=request.organizer
    ).order_by('-created_at')
    
    # Mark all as read
    notifications.filter(is_read=False).update(is_read=True)
    
    return render(request, 'organizers/notifications.html', {
        'notifications': notifications
    })


@login_required
@organizer_required
def payouts(request):
    """View payout history"""
    payouts = OrganizerPayout.objects.filter(
        organizer=request.organizer
    ).order_by('-requested_at')
    
    return render(request, 'organizers/payouts.html', {
        'payouts': payouts
    })


@login_required
@organizer_required
def ticket_management(request):
    events = Event.objects.filter(organizer=request.organizer.user)
    tickets = TicketType.objects.filter(event__in=events).select_related('event').order_by('-event__start_date')
    return render(request, 'organizers/ticket_management.html', {
        'tickets': tickets,
        'events': events,
    })


# =============================================================================
# Registration Management Views
# =============================================================================

@login_required
@organizer_required
def registration_list(request):
    """List all registrations for organizer's events with filtering"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    # Base queryset
    registrations = Registration.objects.filter(event__in=events).select_related(
        'event', 'ticket_type', 'user', 'promo_code'
    ).prefetch_related('checkins')
    
    # Get filter parameters
    event_id = request.GET.get('event')
    status = request.GET.get('status')
    ticket_type_id = request.GET.get('ticket_type')
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Apply filters
    if event_id:
        registrations = registrations.filter(event_id=event_id)
    if status:
        registrations = registrations.filter(status=status)
    if ticket_type_id:
        registrations = registrations.filter(ticket_type_id=ticket_type_id)
    if search:
        registrations = registrations.filter(
            Q(attendee_name__icontains=search) |
            Q(attendee_email__icontains=search) |
            Q(registration_number__icontains=search)
        )
    if date_from:
        registrations = registrations.filter(created_at__date__gte=date_from)
    if date_to:
        registrations = registrations.filter(created_at__date__lte=date_to)
    
    # Calculate statistics
    total_registrations = registrations.count()
    total_revenue = registrations.filter(
        status__in=['confirmed', 'checked_in']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    checked_in_count = registrations.filter(status='checked_in').count()
    pending_count = registrations.filter(status='pending').count()
    
    # Get all ticket types for filter dropdown
    ticket_types = TicketType.objects.filter(event__in=events)
    
    # Pagination
    paginator = Paginator(registrations.order_by('-created_at'), 25)
    page = request.GET.get('page')
    registrations_page = paginator.get_page(page)
    
    context = {
        'registrations': registrations_page,
        'events': events,
        'ticket_types': ticket_types,
        'total_registrations': total_registrations,
        'total_revenue': total_revenue,
        'checked_in_count': checked_in_count,
        'pending_count': pending_count,
        'filters': {
            'event': event_id,
            'status': status,
            'ticket_type': ticket_type_id,
            'search': search,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'organizers/registration_list.html', context)


@login_required
@organizer_required
def event_registration_list(request, event_id):
    """List registrations for a specific event"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    
    registrations = Registration.objects.filter(event=event).select_related(
        'ticket_type', 'user', 'promo_code'
    ).prefetch_related('checkins')
    
    # Apply same filters as registration_list
    status = request.GET.get('status')
    ticket_type_id = request.GET.get('ticket_type')
    search = request.GET.get('search')
    
    if status:
        registrations = registrations.filter(status=status)
    if ticket_type_id:
        registrations = registrations.filter(ticket_type_id=ticket_type_id)
    if search:
        registrations = registrations.filter(
            Q(attendee_name__icontains=search) |
            Q(attendee_email__icontains=search)
        )
    
    # Statistics
    total_registrations = registrations.count()
    total_revenue = registrations.filter(
        status__in=['confirmed', 'checked_in']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    checked_in_count = registrations.filter(status='checked_in').count()
    pending_count = registrations.filter(status='pending').count()
    
    ticket_types = TicketType.objects.filter(event=event)
    
    paginator = Paginator(registrations.order_by('-created_at'), 25)
    page = request.GET.get('page')
    registrations_page = paginator.get_page(page)
    
    context = {
        'registrations': registrations_page,
        'event': event,
        'events': Event.objects.filter(organizer=request.user),
        'ticket_types': ticket_types,
        'total_registrations': total_registrations,
        'total_revenue': total_revenue,
        'checked_in_count': checked_in_count,
        'pending_count': pending_count,
        'is_event_specific': True,
    }
    return render(request, 'organizers/registration_list.html', context)


@login_required
@organizer_required
def registration_detail(request, registration_id):
    """View registration details"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    registration = get_object_or_404(
        Registration.objects.select_related('event', 'ticket_type', 'user', 'promo_code'),
        id=registration_id,
        event__in=events
    )
    
    # Get check-in history
    checkins = CheckIn.objects.filter(registration=registration).select_related('checked_in_by')
    
    # Get custom field responses
    custom_responses = registration.custom_fields or {}
    
    # Generate QR code
    qr_code_base64 = registration.generate_qr_code_image()
    
    context = {
        'registration': registration,
        'checkins': checkins,
        'custom_responses': custom_responses,
        'qr_code': qr_code_base64,
    }
    return render(request, 'organizers/registration_detail.html', context)


@login_required
@organizer_required
def registration_edit(request, registration_id):
    """Edit registration details"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    registration = get_object_or_404(
        Registration,
        id=registration_id,
        event__in=events
    )
    
    if request.method == 'POST':
        form = RegistrationEditForm(request.POST, instance=registration)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration updated successfully!')
            return redirect('organizer_registration_detail', registration_id=registration.id)
    else:
        form = RegistrationEditForm(instance=registration)
    
    context = {
        'form': form,
        'registration': registration,
        'title': 'Edit Registration',
    }
    return render(request, 'organizers/registration_form.html', context)


@login_required
@organizer_required
def registration_cancel(request, registration_id):
    """Cancel a registration"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    registration = get_object_or_404(
        Registration,
        id=registration_id,
        event__in=events
    )
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        registration.cancel(reason=reason)
        messages.success(request, f'Registration {registration.registration_number} has been cancelled.')
        return redirect('organizer_registration_list')
    
    return render(request, 'organizers/registration_cancel.html', {
        'registration': registration,
    })


@login_required
@organizer_required
def registration_checkin(request, registration_id):
    """Manually check in a registration"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    registration = get_object_or_404(
        Registration,
        id=registration_id,
        event__in=events
    )
    
    if registration.status in ['confirmed', 'pending']:
        registration.check_in(checked_by=request.user)
        CheckIn.objects.create(
            registration=registration,
            checked_in_by=request.user,
            method='manual',
            notes=request.POST.get('notes', '')
        )
        messages.success(request, f'{registration.attendee_name} has been checked in successfully!')
    else:
        messages.error(request, 'Cannot check in this registration. Invalid status.')
    
    return redirect('organizer_registration_detail', registration_id=registration.id)


@login_required
@organizer_required
def registration_refund(request, registration_id):
    """Process refund for a registration"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    registration = get_object_or_404(
        Registration,
        id=registration_id,
        event__in=events
    )
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        reason = request.POST.get('reason', '')
        
        try:
            refund_amount = Decimal(amount) if amount else None
            if registration.refund(amount=refund_amount, reason=reason):
                messages.success(request, f'Refund processed for {registration.registration_number}.')
            else:
                messages.error(request, 'Could not process refund. Registration may not be eligible.')
        except Exception as e:
            messages.error(request, f'Error processing refund: {str(e)}')
        
        return redirect('organizer_registration_detail', registration_id=registration.id)
    
    return render(request, 'organizers/registration_refund.html', {
        'registration': registration,
    })


@login_required
@organizer_required
def registration_resend_ticket(request, registration_id):
    """Resend ticket email to attendee"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    registration = get_object_or_404(
        Registration,
        id=registration_id,
        event__in=events
    )
    
    # Send ticket email logic here
    # For now, just show success message
    messages.success(request, f'Ticket resent to {registration.attendee_email}.')
    
    return redirect('organizer_registration_detail', registration_id=registration.id)


@login_required
@organizer_required
def registration_export(request):
    """Export registrations to CSV or Excel"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    # Get filter parameters
    event_id = request.GET.get('event')
    status = request.GET.get('status')
    format_type = request.GET.get('format', 'csv')
    
    registrations = Registration.objects.filter(event__in=events).select_related(
        'event', 'ticket_type', 'promo_code'
    )
    
    if event_id:
        registrations = registrations.filter(event_id=event_id)
    if status:
        registrations = registrations.filter(status=status)
    
    if format_type == 'excel':
        return _export_excel(registrations)
    else:
        return _export_csv(registrations)


def _export_csv(registrations):
    """Helper function to export registrations as CSV"""
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="registrations.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Registration ID', 'Event', 'Attendee Name', 'Email', 'Phone',
        'Ticket Type', 'Status', 'Amount', 'Discount', 'Promo Code',
        'Registration Date', 'Checked In', 'Checked In At'
    ])
    
    for reg in registrations:
        writer.writerow([
            reg.registration_number,
            reg.event.title,
            reg.attendee_name,
            reg.attendee_email,
            reg.attendee_phone,
            reg.ticket_type.name if reg.ticket_type else 'N/A',
            reg.status,
            reg.total_amount,
            reg.discount_amount,
            reg.promo_code.code if reg.promo_code else '',
            reg.created_at.strftime('%Y-%m-%d %H:%M'),
            'Yes' if reg.status == 'checked_in' else 'No',
            reg.checked_in_at.strftime('%Y-%m-%d %H:%M') if reg.checked_in_at else ''
        ])
    
    return response


def _export_excel(registrations):
    """Helper function to export registrations as Excel"""
    # For simplicity, return CSV with different filename
    # In production, use openpyxl or similar
    response = _export_csv(registrations)
    response['Content-Disposition'] = 'attachment; filename="registrations.csv"'
    return response


@login_required
@organizer_required
def registration_bulk_action(request):
    """Handle bulk actions on registrations"""
    if request.method != 'POST':
        return redirect('organizer_registration_list')
    
    action = request.POST.get('action')
    registration_ids = request.POST.getlist('registration_ids')
    
    if not registration_ids:
        messages.warning(request, 'No registrations selected.')
        return redirect('organizer_registration_list')
    
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    registrations = Registration.objects.filter(
        id__in=registration_ids,
        event__in=events
    )
    
    if action == 'checkin':
        count = 0
        for reg in registrations:
            if reg.status in ['confirmed', 'pending']:
                reg.check_in(checked_by=request.user)
                CheckIn.objects.create(
                    registration=reg,
                    checked_in_by=request.user,
                    method='bulk'
                )
                count += 1
        messages.success(request, f'{count} attendees checked in successfully.')
    
    elif action == 'cancel':
        count = 0
        for reg in registrations:
            if reg.status in ['pending', 'confirmed']:
                reg.cancel(reason='Bulk cancellation by organizer')
                count += 1
        messages.success(request, f'{count} registrations cancelled.')
    
    elif action == 'email':
        # Store selected IDs in session for email composition
        request.session['bulk_email_registration_ids'] = registration_ids
        messages.info(request, f'{len(registration_ids)} registrations selected. Redirecting to email composition...')
        # Redirect to communication app email composition
        return redirect('communication:bulk_email') if False else redirect('organizer_registration_list')
    
    elif action == 'export':
        return _export_csv(registrations)
    
    return redirect('organizer_registration_list')


# =============================================================================
# Communication Management Views
# =============================================================================

@login_required
@organizer_required
def communication_dashboard(request):
    """Communication dashboard with overview of all communication features"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    # Statistics
    total_email_logs = EmailLog.objects.filter(event__in=events).count()
    total_scheduled = ScheduledEmail.objects.filter(event__in=events, is_active=True).count()
    total_polls = LivePoll.objects.filter(event__in=events).count()
    total_qa = LiveQA.objects.filter(event__in=events).count()
    
    # Recent activity
    recent_emails = EmailLog.objects.filter(event__in=events).order_by('-created_at')[:10]
    upcoming_scheduled = ScheduledEmail.objects.filter(
        event__in=events, 
        is_active=True,
        scheduled_at__gte=timezone.now()
    ).order_by('scheduled_at')[:5]
    
    # Active polls
    active_polls = LivePoll.objects.filter(
        event__in=events,
        is_active=True
    ).order_by('-created_at')[:5]
    
    context = {
        'total_email_logs': total_email_logs,
        'total_scheduled': total_scheduled,
        'total_polls': total_polls,
        'total_qa': total_qa,
        'recent_emails': recent_emails,
        'upcoming_scheduled': upcoming_scheduled,
        'active_polls': active_polls,
        'events': events,
    }
    return render(request, 'organizers/communication_dashboard.html', context)


@login_required
@organizer_required
def email_template_list(request):
    """List all email templates"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    templates = EmailTemplate.objects.filter(is_active=True)
    
    context = {
        'templates': templates,
    }
    return render(request, 'organizers/email_template_list.html', context)


@login_required
@organizer_required
def email_template_create(request):
    """Create a new email template"""
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email template created successfully!')
            return redirect('organizer_email_template_list')
    else:
        form = EmailTemplateForm()
    
    return render(request, 'organizers/email_template_form.html', {
        'form': form,
        'title': 'Create Email Template',
        'action': 'Create'
    })


@login_required
@organizer_required
def email_template_edit(request, template_id):
    """Edit an existing email template"""
    template = get_object_or_404(EmailTemplate, id=template_id)
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email template updated successfully!')
            return redirect('organizer_email_template_list')
    else:
        form = EmailTemplateForm(instance=template)
    
    return render(request, 'organizers/email_template_form.html', {
        'form': form,
        'template': template,
        'title': 'Edit Email Template',
        'action': 'Save Changes'
    })


@login_required
@organizer_required
def scheduled_email_list(request):
    """List all scheduled emails"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    scheduled_emails = ScheduledEmail.objects.filter(
        event__in=events
    ).select_related('event', 'template').order_by('-created_at')
    
    context = {
        'scheduled_emails': scheduled_emails,
        'events': events,
    }
    return render(request, 'organizers/scheduled_email_list.html', context)


@login_required
@organizer_required
def scheduled_email_create(request):
    """Create a new scheduled email"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    templates = EmailTemplate.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = ScheduledEmailForm(request.POST)
        if form.is_valid():
            scheduled_email = form.save(commit=False)
            # Ensure event belongs to organizer
            if scheduled_email.event.organizer != organizer.user:
                messages.error(request, 'You do not have permission to schedule emails for this event.')
                return redirect('organizer_scheduled_email_list')
            scheduled_email.save()
            messages.success(request, 'Scheduled email created successfully!')
            return redirect('organizer_scheduled_email_list')
    else:
        form = ScheduledEmailForm()
        # Filter events to organizer's events
        form.fields['event'].queryset = events
    
    context = {
        'form': form,
        'title': 'Schedule Email',
        'action': 'Schedule',
        'events': events,
        'templates': templates,
    }
    return render(request, 'organizers/scheduled_email_form.html', context)


@login_required
@organizer_required
def scheduled_email_edit(request, email_id):
    """Edit a scheduled email"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    scheduled_email = get_object_or_404(
        ScheduledEmail,
        id=email_id,
        event__in=events
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            scheduled_email.delete()
            messages.success(request, 'Scheduled email deleted successfully!')
            return redirect('organizer_scheduled_email_list')
        
        form = ScheduledEmailForm(request.POST, instance=scheduled_email)
        if form.is_valid():
            form.save()
            messages.success(request, 'Scheduled email updated successfully!')
            return redirect('organizer_scheduled_email_list')
    else:
        form = ScheduledEmailForm(instance=scheduled_email)
        form.fields['event'].queryset = events
    
    return render(request, 'organizers/scheduled_email_form.html', {
        'form': form,
        'scheduled_email': scheduled_email,
        'title': 'Edit Scheduled Email',
        'action': 'Save Changes',
        'events': events,
    })


@login_required
@organizer_required
def send_email(request):
    """Send email to attendees"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    templates = EmailTemplate.objects.filter(is_active=True)
    
    if request.method == 'POST':
        event_id = request.POST.get('event')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        recipient_filter = request.POST.get('recipient_filter', '{}')
        
        if not event_id or not subject or not content:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('organizer_send_email')
        
        try:
            import json
            recipient_filter = json.loads(recipient_filter) if recipient_filter else {}
        except json.JSONDecodeError:
            recipient_filter = {}
        
        event = get_object_or_404(Event, id=event_id, organizer=organizer.user)
        
        # Get recipients based on filter
        from registration.models import Registration
        registrations = Registration.objects.filter(event=event)
        
        if recipient_filter.get('status'):
            registrations = registrations.filter(status=recipient_filter['status'])
        
        # Send emails
        sent_count = 0
        for reg in registrations:
            try:
                EmailLog.objects.create(
                    recipient=reg.attendee_email,
                    event=event,
                    subject=subject,
                    content=content,
                    status='pending'
                )
                sent_count += 1
            except Exception:
                pass
        
        messages.success(request, f'Email queued for {sent_count} recipients.')
        return redirect('organizer_email_log_list')
    
    context = {
        'events': events,
        'templates': templates,
    }
    return render(request, 'organizers/send_email.html', context)


@login_required
@organizer_required
def email_log_list(request):
    """List email logs"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    # Get filter parameters
    event_id = request.GET.get('event')
    status = request.GET.get('status')
    
    email_logs = EmailLog.objects.filter(event__in=events).select_related('event', 'template')
    
    if event_id:
        email_logs = email_logs.filter(event_id=event_id)
    if status:
        email_logs = email_logs.filter(status=status)
    
    # Pagination
    paginator = Paginator(email_logs.order_by('-created_at'), 50)
    page = request.GET.get('page')
    email_logs_page = paginator.get_page(page)
    
    context = {
        'email_logs': email_logs_page,
        'events': events,
        'status_choices': EmailLog.STATUS_CHOICES,
        'filters': {
            'event': event_id,
            'status': status,
        }
    }
    return render(request, 'organizers/email_log_list.html', context)


@login_required
@organizer_required
def live_poll_list(request):
    """List all live polls"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    polls = LivePoll.objects.filter(event__in=events).select_related('event', 'session').order_by('-created_at')
    
    context = {
        'polls': polls,
        'events': events,
    }
    return render(request, 'organizers/live_poll_list.html', context)


@login_required
@organizer_required
def live_poll_create(request):
    """Create a new live poll"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    if request.method == 'POST':
        form = LivePollForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            if poll.event.organizer != organizer.user:
                messages.error(request, 'You do not have permission to create polls for this event.')
                return redirect('organizer_live_poll_list')
            
            # Process options for single/multiple choice
            if poll.poll_type in ['single', 'multiple']:
                options_text = request.POST.get('options_text', '')
                if options_text:
                    poll.options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
            
            poll.save()
            messages.success(request, 'Live poll created successfully!')
            return redirect('organizer_live_poll_list')
    else:
        form = LivePollForm()
        form.fields['event'].queryset = events
    
    return render(request, 'organizers/live_poll_form.html', {
        'form': form,
        'title': 'Create Live Poll',
        'action': 'Create',
        'events': events,
    })


@login_required
@organizer_required
def live_poll_detail(request, poll_id):
    """View live poll details and results"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    poll = get_object_or_404(
        LivePoll.objects.select_related('event', 'session'),
        id=poll_id,
        event__in=events
    )
    
    responses = poll.responses.select_related('user')
    response_count = responses.count()
    
    # Calculate results
    results = {}
    if poll.poll_type in ['single', 'multiple']:
        for option in poll.options:
            results[option] = responses.filter(selected_options__contains=[option]).count()
    elif poll.poll_type == 'rating':
        ratings = [r.rating_value for r in responses if r.rating_value]
        results = {
            'average': sum(ratings) / len(ratings) if ratings else 0,
            'distribution': {i: responses.filter(rating_value=i).count() for i in range(1, 6)}
        }
    elif poll.poll_type == 'wordcloud':
        words = {}
        for r in responses:
            if r.wordcloud_response:
                words[r.wordcloud_response] = words.get(r.wordcloud_response, 0) + 1
        results = dict(sorted(words.items(), key=lambda x: x[1], reverse=True)[:20])
    
    context = {
        'poll': poll,
        'responses': responses,
        'response_count': response_count,
        'results': results,
    }
    return render(request, 'organizers/live_poll_detail.html', context)


@login_required
@organizer_required
def live_qa_list(request):
    """List all live Q&A sessions"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    # Get sessions with Q&A
    sessions = EventSession.objects.filter(
        event__in=events,
        qa_questions__isnull=False
    ).distinct().select_related('event').order_by('-start_time')
    
    # Get recent questions
    recent_questions = LiveQA.objects.filter(
        event__in=events
    ).select_related('event', 'session', 'user').order_by('-created_at')[:20]
    
    context = {
        'sessions': sessions,
        'recent_questions': recent_questions,
        'events': events,
    }
    return render(request, 'organizers/live_qa_list.html', context)


@login_required
@organizer_required
def live_qa_session(request, session_id):
    """View and moderate Q&A for a specific session"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    session = get_object_or_404(
        EventSession.objects.select_related('event'),
        id=session_id,
        event__in=events
    )
    
    questions = LiveQA.objects.filter(
        session=session
    ).select_related('user', 'answered_by').order_by('-upvotes', '-created_at')
    
    pending_count = questions.filter(is_approved=False).count()
    answered_count = questions.filter(is_answered=True).count()
    
    context = {
        'session': session,
        'questions': questions,
        'pending_count': pending_count,
        'answered_count': answered_count,
        'total_count': questions.count(),
    }
    return render(request, 'organizers/live_qa_session.html', context)


# =============================================================================
# Sponsor Management Views
# =============================================================================

@login_required
@organizer_required
def sponsor_list(request):
    """List all sponsors for organizer's events"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    # Get filter parameters
    event_id = request.GET.get('event')
    tier = request.GET.get('tier')
    
    sponsors = Sponsor.objects.filter(event__in=events).select_related('event')
    
    if event_id:
        sponsors = sponsors.filter(event_id=event_id)
    if tier:
        sponsors = sponsors.filter(tier=tier)
    
    # Statistics
    total_sponsors = sponsors.count()
    sponsors_by_tier = sponsors.values('tier').annotate(count=Count('id'))
    
    context = {
        'sponsors': sponsors.order_by('display_order', 'tier'),
        'events': events,
        'total_sponsors': total_sponsors,
        'sponsors_by_tier': sponsors_by_tier,
        'tier_choices': Sponsor.TIER_CHOICES,
        'filters': {
            'event': event_id,
            'tier': tier,
        }
    }
    return render(request, 'organizers/sponsor_list.html', context)


@login_required
@organizer_required
def event_sponsor_list(request, event_id):
    """List sponsors for a specific event"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    
    sponsors = Sponsor.objects.filter(event=event).select_related('event')
    
    # Statistics
    total_sponsors = sponsors.count()
    sponsors_by_tier = sponsors.values('tier').annotate(count=Count('id'))
    
    context = {
        'sponsors': sponsors.order_by('display_order', 'tier'),
        'event': event,
        'events': Event.objects.filter(organizer=request.user),
        'total_sponsors': total_sponsors,
        'sponsors_by_tier': sponsors_by_tier,
        'tier_choices': Sponsor.TIER_CHOICES,
        'is_event_specific': True,
    }
    return render(request, 'organizers/sponsor_list.html', context)


@login_required
@organizer_required
def sponsor_detail(request, sponsor_id):
    """View sponsor details"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    sponsor = get_object_or_404(
        Sponsor.objects.select_related('event'),
        id=sponsor_id,
        event__in=events
    )
    
    context = {
        'sponsor': sponsor,
    }
    return render(request, 'organizers/sponsor_detail.html', context)


@login_required
@organizer_required
def sponsor_create(request):
    """Create a new sponsor"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES)
        if form.is_valid():
            sponsor = form.save(commit=False)
            # Ensure event belongs to organizer
            if sponsor.event.organizer != organizer.user:
                messages.error(request, 'You do not have permission to add sponsors to this event.')
                return redirect('organizer_sponsor_list')
            sponsor.save()
            messages.success(request, f'Sponsor "{sponsor.company_name}" created successfully!')
            return redirect('organizer_sponsor_detail', sponsor_id=sponsor.id)
    else:
        form = SponsorForm()
        form.fields['event'].queryset = events
    
    return render(request, 'organizers/sponsor_form.html', {
        'form': form,
        'title': 'Add Sponsor',
        'action': 'Create',
        'events': events,
    })


@login_required
@organizer_required
def sponsor_edit(request, sponsor_id):
    """Edit a sponsor"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    sponsor = get_object_or_404(
        Sponsor,
        id=sponsor_id,
        event__in=events
    )
    
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES, instance=sponsor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sponsor "{sponsor.company_name}" updated successfully!')
            return redirect('organizer_sponsor_detail', sponsor_id=sponsor.id)
    else:
        form = SponsorForm(instance=sponsor)
        form.fields['event'].queryset = events
    
    return render(request, 'organizers/sponsor_form.html', {
        'form': form,
        'sponsor': sponsor,
        'title': 'Edit Sponsor',
        'action': 'Save Changes',
        'events': events,
    })


@login_required
@organizer_required
def sponsor_delete(request, sponsor_id):
    """Delete a sponsor"""
    organizer = request.organizer
    events = Event.objects.filter(organizer=organizer.user)
    
    sponsor = get_object_or_404(
        Sponsor,
        id=sponsor_id,
        event__in=events
    )
    
    if request.method == 'POST':
        company_name = sponsor.company_name
        sponsor.delete()
        messages.success(request, f'Sponsor "{company_name}" deleted successfully!')
        return redirect('organizer_sponsor_list')
    
    return render(request, 'organizers/sponsor_confirm_delete.html', {
        'sponsor': sponsor,
    })
