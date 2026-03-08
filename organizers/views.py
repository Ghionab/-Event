from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate

from .models import (
    OrganizerProfile, OrganizerTeamMember, EventAnalytics,
    EventTemplate, OrganizerNotification, OrganizerPayout
)
from events.models import Event
from registration.models import Registration, TicketType


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
            event.save()
            messages.success(request, 'Event created successfully!')
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
    
    # Registration trends
    registrations = Registration.objects.filter(
        event__in=events, status='confirmed'
    ).annotate(date=TruncDate('created_at')).values('date').annotate(
        count=Count('id'), revenue=Sum('total_amount')
    ).order_by('date')
    
    context = {
        'events': events,
        'registrations': registrations,
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
