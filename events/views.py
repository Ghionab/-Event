from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from django.template.loader import render_to_string
from .forms import EventForm, EventSessionForm, SpeakerForm, TrackForm, RoomForm, SponsorForm, SpeakerSessionAssignmentForm
from .models import Event, EventSession, Speaker, Track, Room, Sponsor
from registration.models import TicketType
import csv
from datetime import datetime

# Create your views here.

def home(request):
    # Get only public published events
    events = Event.objects.filter(is_public=True, status='published').order_by('-start_date')
    return render(request, 'events/home.html', {'events': events})

def event_list(request):
    # Get only public published events
    events = Event.objects.filter(is_public=True, status='published').order_by('-start_date')
    return render(request, 'events/event_list.html', {'events': events})

@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.status = 'draft'  # Auto-assign draft status
            event.save()
            
            # Send email invitations if provided
            invite_emails = form.cleaned_data.get('invite_emails', [])
            if invite_emails:
                sent_count = send_event_invitations(event, invite_emails, request.user)
                if sent_count > 0:
                    messages.success(request, f'Event created! Sent {sent_count} invitation(s).')
                else:
                    messages.warning(request, 'Event created, but failed to send invitations.')
            else:
                messages.success(request, 'Event created successfully!')
            
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form})


def send_event_invitations(event, email_list, organizer):
    """Send invitation emails for an event"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    sent_count = 0
    
    # Build registration URL
    registration_url = f"http://localhost:8001/events/{event.id}/"
    
    for email in email_list:
        subject = f"You're Invited: {event.title}"
        
        message = f"""
Dear Guest,

You have been invited to attend {event.title}!

Event Details:
- Event: {event.title}
- Date: {event.start_date.strftime('%B %d, %Y at %I:%M %p')}
- Venue: {event.venue_name or 'TBA'}
- Location: {event.city}, {event.country}

{event.description[:200]}...

Register now: {registration_url}

Best regards,
{organizer.get_full_name() or organizer.username}
{event.contact_email or ''}
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            sent_count += 1
        except Exception as e:
            # Log error but continue with other emails
            print(f"Failed to send invitation to {email}: {str(e)}")
    
    return sent_count

def event_detail(request, event_id):
    from registration.forms import RegistrationForm
    from registration.models import Registration
    event = get_object_or_404(Event, id=event_id, is_public=True)
    # Get organizer profile for branding
    organizer_profile = None
    try:
        organizer_profile = event.organizer.organizer_profile
    except Exception:
        pass
    ticket_types = TicketType.objects.filter(event=event, is_active=True)
    registration_success = False
    registration_errors = None
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        form.fields['ticket_type'].queryset = ticket_types
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.user = request.user if request.user.is_authenticated else None
            registration.save()
            registration_success = True
        else:
            registration_errors = form.errors
    else:
        form = RegistrationForm()
        form.fields['ticket_type'].queryset = ticket_types
    return render(request, 'events/event_detail.html', {
        'event': event,
        'ticket_types': ticket_types,
        'form': form,
        'registration_success': registration_success,
        'registration_errors': registration_errors,
        'organizer_profile': organizer_profile,
    })

def event_landing(request, slug):
    """Public event landing page with SEO-friendly URL"""
    from registration.forms import RegistrationForm
    event = get_object_or_404(Event, slug=slug, is_public=True, status='published')
    # Get organizer profile for branding
    organizer_profile = None
    try:
        organizer_profile = event.organizer.organizer_profile
    except Exception:
        pass
    ticket_types = TicketType.objects.filter(event=event, is_active=True)
    registration_success = False
    registration_errors = None
    sessions = event.sessions.filter(is_public=True).order_by('start_time')
    speakers = event.speakers.filter(is_confirmed=True).order_by('display_order')
    sponsors = event.sponsors.filter(is_featured=True).order_by('display_order')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        form.fields['ticket_type'].queryset = ticket_types
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.user = request.user if request.user.is_authenticated else None
            registration.save()
            registration_success = True
        else:
            registration_errors = form.errors
    else:
        form = RegistrationForm()
        form.fields['ticket_type'].queryset = ticket_types
    return render(request, 'events/event_landing.html', {
        'event': event,
        'ticket_types': ticket_types,
        'form': form,
        'registration_success': registration_success,
        'registration_errors': registration_errors,
        'organizer_profile': organizer_profile,
        'sessions': sessions,
        'speakers': speakers,
        'sponsors': sponsors,
    })

def event_edit(request, event_id):
    """Edit an existing event"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user has permission to edit
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to edit events.')
        return redirect('login')
    
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/event_form.html', {'form': form, 'event': event, 'title': 'Edit Event'})

def event_delete(request, event_id):
    """Delete an event"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check if user has permission to delete
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to delete events.')
        return redirect('login')
    
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" has been deleted.')
        return redirect('event_list')
    
    return render(request, 'events/event_confirm_delete.html', {'event': event})

@login_required
def session_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    sessions = event.sessions.order_by('start_time')
    tracks = event.tracks.all()
    return render(request, 'events/session_list.html', {'event': event, 'sessions': sessions, 'tracks': tracks})

@login_required
def session_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventSessionForm(request.POST, event=event)
        if form.is_valid():
            session = form.save(commit=False)
            session.event = event
            session.save()
            messages.success(request, 'Session created successfully!')
            return redirect('session_list', event_id=event.id)
    else:
        form = EventSessionForm(event=event)
    return render(request, 'events/session_form.html', {'form': form, 'event': event})

@login_required
def session_edit(request, event_id, session_id):
    event = get_object_or_404(Event, id=event_id)
    session = get_object_or_404(EventSession, id=session_id, event=event)
    if request.method == 'POST':
        form = EventSessionForm(request.POST, event=event, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Session updated successfully!')
            return redirect('session_list', event_id=event.id)
    else:
        form = EventSessionForm(event=event, instance=session)
    return render(request, 'events/session_form.html', {'form': form, 'event': event, 'session': session})

@login_required
def session_delete(request, event_id, session_id):
    event = get_object_or_404(Event, id=event_id)
    session = get_object_or_404(EventSession, id=session_id, event=event)
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Session deleted successfully!')
        return redirect('session_list', event_id=event.id)
    return render(request, 'events/session_confirm_delete.html', {'event': event, 'session': session})

# Speaker Views
@login_required
def speaker_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    speakers = event.speakers.order_by('display_order')
    return render(request, 'events/speaker_list.html', {'event': event, 'speakers': speakers})

@login_required
def speaker_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = SpeakerForm(request.POST, request.FILES)
        if form.is_valid():
            speaker = form.save(commit=False)
            speaker.event = event
            speaker.save()
            messages.success(request, 'Speaker added successfully!')
            return redirect('speaker_list', event_id=event.id)
    else:
        form = SpeakerForm()
    return render(request, 'events/speaker_form.html', {'form': form, 'event': event})

@login_required
def speaker_edit(request, event_id, speaker_id):
    event = get_object_or_404(Event, id=event_id)
    speaker = get_object_or_404(Speaker, id=speaker_id, event=event)
    if request.method == 'POST':
        form = SpeakerForm(request.POST, request.FILES, instance=speaker)
        if form.is_valid():
            form.save()
            messages.success(request, 'Speaker updated successfully!')
            return redirect('speaker_list', event_id=event.id)
    else:
        form = SpeakerForm(instance=speaker)
    return render(request, 'events/speaker_form.html', {'form': form, 'event': event, 'speaker': speaker})

@login_required
def speaker_delete(request, event_id, speaker_id):
    event = get_object_or_404(Event, id=event_id)
    speaker = get_object_or_404(Speaker, id=speaker_id, event=event)
    if request.method == 'POST':
        speaker.delete()
        messages.success(request, 'Speaker deleted successfully!')
        return redirect('speaker_list', event_id=event.id)
    return render(request, 'events/speaker_confirm_delete.html', {'event': event, 'speaker': speaker})

@login_required
def speaker_assign_sessions(request, event_id, speaker_id):
    event = get_object_or_404(Event, id=event_id)
    speaker = get_object_or_404(Speaker, id=speaker_id, event=event)
    if request.method == 'POST':
        form = SpeakerSessionAssignmentForm(request.POST, event=event, session=speaker)
        if form.is_valid():
            speaker.sessions.set(form.cleaned_data['speakers'])
            messages.success(request, 'Sessions assigned successfully!')
            return redirect('speaker_list', event_id=event.id)
    else:
        form = SpeakerSessionAssignmentForm(event=event, session=speaker)
    return render(request, 'events/speaker_assign_sessions.html', {'form': form, 'event': event, 'speaker': speaker})

# Track Views
@login_required
def track_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    tracks = event.tracks.order_by('order')
    return render(request, 'events/track_list.html', {'event': event, 'tracks': tracks})

@login_required
def track_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = TrackForm(request.POST)
        if form.is_valid():
            track = form.save(commit=False)
            track.event = event
            track.save()
            messages.success(request, 'Track created successfully!')
            return redirect('track_list', event_id=event.id)
    else:
        form = TrackForm()
    return render(request, 'events/track_form.html', {'form': form, 'event': event})

@login_required
def track_edit(request, event_id, track_id):
    event = get_object_or_404(Event, id=event_id)
    track = get_object_or_404(Track, id=track_id, event=event)
    if request.method == 'POST':
        form = TrackForm(request.POST, instance=track)
        if form.is_valid():
            form.save()
            messages.success(request, 'Track updated successfully!')
            return redirect('track_list', event_id=event.id)
    else:
        form = TrackForm(instance=track)
    return render(request, 'events/track_form.html', {'form': form, 'event': event, 'track': track})

@login_required
def track_delete(request, event_id, track_id):
    event = get_object_or_404(Event, id=event_id)
    track = get_object_or_404(Track, id=track_id, event=event)
    if request.method == 'POST':
        track.delete()
        messages.success(request, 'Track deleted successfully!')
        return redirect('track_list', event_id=event.id)
    return render(request, 'events/track_confirm_delete.html', {'event': event, 'track': track})

# Room Views
@login_required
def room_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    rooms = event.rooms.order_by('order')
    return render(request, 'events/room_list.html', {'event': event, 'rooms': rooms})

@login_required
def room_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.event = event
            room.save()
            messages.success(request, 'Room created successfully!')
            return redirect('room_list', event_id=event.id)
    else:
        form = RoomForm()
    return render(request, 'events/room_form.html', {'form': form, 'event': event})

@login_required
def room_edit(request, event_id, room_id):
    event = get_object_or_404(Event, id=event_id)
    room = get_object_or_404(Room, id=room_id, event=event)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully!')
            return redirect('room_list', event_id=event.id)
    else:
        form = RoomForm(instance=room)
    return render(request, 'events/room_form.html', {'form': form, 'event': event, 'room': room})

@login_required
def room_delete(request, event_id, room_id):
    event = get_object_or_404(Event, id=event_id)
    room = get_object_or_404(Room, id=room_id, event=event)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully!')
        return redirect('room_list', event_id=event.id)
    return render(request, 'events/room_confirm_delete.html', {'event': event, 'room': room})

# Sponsor Views
@login_required
def sponsor_list(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    sponsors = event.sponsors.order_by('display_order')
    return render(request, 'events/sponsor_list.html', {'event': event, 'sponsors': sponsors})

@login_required
def sponsor_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES)
        if form.is_valid():
            sponsor = form.save(commit=False)
            sponsor.event = event
            sponsor.save()
            messages.success(request, 'Sponsor added successfully!')
            return redirect('sponsor_list', event_id=event.id)
    else:
        form = SponsorForm()
    return render(request, 'events/sponsor_form.html', {'form': form, 'event': event})

@login_required
def sponsor_edit(request, event_id, sponsor_id):
    event = get_object_or_404(Event, id=event_id)
    sponsor = get_object_or_404(Sponsor, id=sponsor_id, event=event)
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES, instance=sponsor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sponsor updated successfully!')
            return redirect('sponsor_list', event_id=event.id)
    else:
        form = SponsorForm(instance=sponsor)
    return render(request, 'events/sponsor_form.html', {'form': form, 'event': event, 'sponsor': sponsor})

@login_required
def sponsor_delete(request, event_id, sponsor_id):
    event = get_object_or_404(Event, id=event_id)
    sponsor = get_object_or_404(Sponsor, id=sponsor_id, event=event)
    if request.method == 'POST':
        sponsor.delete()
        messages.success(request, 'Sponsor deleted successfully!')
        return redirect('sponsor_list', event_id=event.id)
    return render(request, 'events/sponsor_confirm_delete.html', {'event': event, 'sponsor': sponsor})

# Export Views
@login_required
def export_agenda(request, event_id):
    """Export agenda as CSV"""
    event = get_object_or_404(Event, id=event_id)
    sessions = event.sessions.order_by('start_time')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="agenda_{event.slug}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Description', 'Date', 'Start Time', 'End Time', 'Location', 'Track', 'Session Type', 'Capacity'])
    
    for session in sessions:
        writer.writerow([
            session.title,
            session.description,
            session.start_time.strftime('%Y-%m-%d'),
            session.start_time.strftime('%H:%M'),
            session.end_time.strftime('%H:%M'),
            session.location,
            session.track.name if session.track else '',
            session.get_session_type_display(),
            session.capacity or '',
        ])
    
    return response

@login_required
def export_speakers(request, event_id):
    """Export speakers as CSV"""
    event = get_object_or_404(Event, id=event_id)
    speakers = event.speakers.order_by('name')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="speakers_{event.slug}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Job Title', 'Company', 'Bio', 'Website', 'Twitter', 'LinkedIn', 'Confirmed', 'Featured'])
    
    for speaker in speakers:
        writer.writerow([
            speaker.name,
            speaker.email,
            speaker.job_title,
            speaker.company,
            speaker.bio,
            speaker.website,
            speaker.twitter,
            speaker.linkedin,
            'Yes' if speaker.is_confirmed else 'No',
            'Yes' if speaker.is_featured else 'No',
        ])
    
    return response

@login_required
def export_sessions_ical(request, event_id):
    """Export sessions as iCal format"""
    from django.utils import timezone
    import icalendar
    
    event = get_object_or_404(Event, id=event_id)
    sessions = event.sessions.order_by('start_time')
    
    cal = icalendar.Calendar()
    cal.add('prodid', '-//Event Management System//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f"{event.title} Agenda")
    
    for session in sessions:
        vevent = icalendar.Event()
        vevent.add('summary', session.title)
        vevent.add('description', session.description)
        vevent.add('dtstart', session.start_time)
        vevent.add('dtend', session.end_time)
        if session.location:
            vevent.add('location', session.location)
        cal.add_component(vevent)
    
    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="agenda_{event.slug}.ics"'
    return response
