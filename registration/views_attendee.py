"""
Attendee-specific views for enhanced attendee experience
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from urllib.parse import quote

from .models import (
    Registration, RegistrationStatus, AttendeePreference,
    SessionAttendance, AttendeeMessage, Badge, AttendeeNotification,
    TicketType
)
from events.models import Event, EventSession, Speaker
from users.models import User
from django.db.models import Count, F, Q, ExpressionWrapper, IntegerField


# =============================================================================
# PRIORITY 1: Core Attendee Dashboard
# =============================================================================

@login_required
def attendee_dashboard(request):
    """Enhanced attendee dashboard with comprehensive overview and popular events.
    Shows events where user is attendee, purchaser, or email matches."""
    user = request.user
    now = timezone.now()
    
    # 1. USER'S EVENTS (as attendee, purchaser, or email match)
    all_registrations = Registration.objects.filter(
        models.Q(purchaser=user) | models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
    ).select_related('event', 'ticket_type').order_by('-created_at')
    
    upcoming_registrations_qs = all_registrations.filter(
        event__start_date__gte=now,
        status__in=[
            RegistrationStatus.PENDING, 
            RegistrationStatus.CONFIRMED, 
            RegistrationStatus.CHECKED_IN,
            RegistrationStatus.WAITLISTED
        ]
    )
    upcoming_registrations = upcoming_registrations_qs[:5]

    # 2. POPULAR & TRENDING EVENTS
    # Logic: Score = (total_tickets_sold * 2) + views_count
    # We annotate the queryset with the ticket count
    popular_events = Event.objects.filter(
        status='published',
        is_public=True,
        start_date__gte=now
    ).annotate(
        tickets_sold=Count('registrations', filter=Q(registrations__status__in=['confirmed', 'checked_in'])),
    ).annotate(
        popularity_score=ExpressionWrapper(
            F('tickets_sold') * 2 + F('views_count'),
            output_field=IntegerField()
        )
    ).order_by('-popularity_score', '-created_at')[:6]

    # Add tags and metadata to popular events
    for event in popular_events:
        # Determine Tag
        if event.popularity_score > 50:
            event.popularity_tag = "🔥 Hot Event"
            event.tag_class = "bg-red-100 text-red-700"
        elif event.popularity_score > 20:
            event.popularity_tag = "⭐ Popular"
            event.tag_class = "bg-amber-100 text-amber-700"
        elif event.created_at > now - timedelta(days=7):
            event.popularity_tag = "📈 Trending"
            event.tag_class = "bg-blue-100 text-blue-700"
        else:
            event.popularity_tag = None
        
        # Format price range
        ticket_prices = TicketType.objects.filter(event=event, is_active=True).values_list('price', flat=True)
        if ticket_prices:
            min_p = min(ticket_prices)
            max_p = max(ticket_prices)
            event.price_range = f"${min_p}" if min_p == max_p else f"${min_p} - ${max_p}"
        else:
            event.price_range = "Free"

    # 3. STATS & OTHER DATA
    unread_messages = AttendeeMessage.objects.filter(recipient=user, is_read=False).count()
    
    saved_sessions_count = 0
    for reg in upcoming_registrations:
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            saved_sessions_count += len(prefs.saved_sessions)
    
    stats = {
        'total_events': all_registrations.count(),
        'upcoming_events': upcoming_registrations_qs.count(),
        'past_events': all_registrations.filter(event__start_date__lt=now, status=RegistrationStatus.CHECKED_IN).count(),
        'unread_messages': unread_messages,
        'saved_sessions': saved_sessions_count,
    }

    context = {
        'upcoming_registrations': upcoming_registrations,
        'popular_events': popular_events,
        'stats': stats,
    }
    
    return render(request, 'participant/attendee_dashboard.html', context)


@login_required
def my_registrations_enhanced(request):
    """Enhanced registration list with filtering and search.
    Shows registrations where user is attendee, purchaser, or email matches."""
    user = request.user
    now = timezone.now()
    
    # Get all registrations where user is attendee, purchaser, or email matches
    # This ensures users see tickets they bought for themselves AND for others
    registrations = Registration.objects.filter(
        models.Q(user=user) | 
        models.Q(attendee_email__iexact=user.email) |
        models.Q(purchaser=user)  # Include tickets purchased for others
    ).select_related('event', 'ticket_type').order_by('-created_at')
    
    # Apply filters
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'upcoming':
        registrations = registrations.filter(event__start_date__gte=now)
    elif filter_type == 'past':
        registrations = registrations.filter(event__start_date__lt=now)
    elif filter_type == 'waitlisted':
        registrations = registrations.filter(status='waitlisted')
    elif filter_type == 'cancelled':
        registrations = registrations.filter(status='cancelled')
        
    # Apply search
    search_query = request.GET.get('search', '')
    if search_query:
        registrations = registrations.filter(
            models.Q(event__title__icontains=search_query) |
            models.Q(registration_number__icontains=search_query) |
            models.Q(attendee_name__icontains=search_query)
        )
        
    # Pagination
    paginator = Paginator(registrations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    
    return render(request, 'participant/my_registrations_enhanced.html', context)


@login_required
def registration_detail_enhanced(request, registration_id):
    """Enhanced registration detail view"""
    registration = get_object_or_404(
        Registration.objects.select_related('event', 'ticket_type'),
        id=registration_id
    )
    
    # Check permission (Allow if user is purchaser OR attendee)
    is_purchaser = registration.purchaser == request.user
    is_attendee = registration.user == request.user or registration.attendee_email.lower() == request.user.email.lower()
    
    if not (is_purchaser or is_attendee):
        messages.error(request, 'You do not have permission to view this registration.')
        return redirect('attendee:dashboard')
    
    # Get event sessions
    sessions = registration.event.sessions.all().order_by('start_time')
    
    # Get speakers
    speakers = registration.event.speakers.filter(is_confirmed=True)
    
    # Get dynamic sessions
    dynamic_sessions = registration.event.dynamic_sessions.all().prefetch_related('session_speakers').order_by('created_at')

    
    # Get badge
    badge = getattr(registration, 'badge', None)
    if not badge:
        # Create badge if doesn't exist
        from .models import Badge
        badge = Badge.objects.create(
            registration=registration,
            name=registration.attendee_name,
            badge_type='vip' if registration.ticket_type and registration.ticket_type.ticket_category == 'vip' else 'standard',
            qr_code_data=f"REG:{registration.qr_code}",
        )
    
    # Get QR code image
    qr_code_image = registration.generate_qr_code_image()
    
    # Get attendee preferences
    preferences = AttendeePreference.objects.filter(
        user=request.user,
        event=registration.event
    ).first()
    
    # Get saved sessions
    saved_session_ids = preferences.saved_sessions if preferences else []
    
    display_total_amount = registration.total_amount or 0
    if (not display_total_amount) and registration.ticket_type and registration.ticket_type.price:
        display_total_amount = registration.ticket_type.price

    context = {
        'registration': registration,
        'sessions': sessions,
        'dynamic_sessions': dynamic_sessions,
        'speakers': speakers,
        'badge': badge,

        'qr_code_image': qr_code_image,
        'preferences': preferences,
        'saved_session_ids': saved_session_ids,
        'display_total_amount': display_total_amount,
    }
    
    return render(request, 'participant/registration_detail_enhanced.html', context)


@login_required
def cancel_registration_enhanced(request, registration_id):
    """Cancel a registration with confirmation"""
    registration = get_object_or_404(Registration, id=registration_id)
    
    # Check permission
    if registration.user != request.user and registration.attendee_email.lower() != request.user.email.lower():
        messages.error(request, 'You do not have permission to cancel this registration.')
        return redirect('attendee:dashboard')
    
    # Check if event has started
    if registration.event.start_date < timezone.now():
        messages.error(request, 'Cannot cancel registration for events that have already started.')
        return redirect('attendee:registration_detail', registration_id=registration.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        registration.cancel(reason=reason)
        messages.success(request, 'Registration cancelled successfully.')
        return redirect('attendee:my_registrations')
    
    context = {
        'registration': registration,
    }
    
    return render(request, 'participant/cancel_registration.html', context)


@login_required
def download_ticket(request, registration_id):
    """Download ticket as PDF with premium design matching HTML template using ReportLab"""
    registration = get_object_or_404(Registration, id=registration_id)
    
    # Check permission
    is_purchaser = registration.purchaser == request.user
    is_attendee = registration.user == request.user or registration.attendee_email.lower() == request.user.email.lower()
    
    if not (is_purchaser or is_attendee):
        messages.error(request, 'You do not have permission to download this ticket.')
        return redirect('attendee:dashboard')

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.units import mm
        from io import BytesIO
        import base64
        import qrcode
        from PIL import Image

        def safe_hex(value, fallback):
            if isinstance(value, str) and value.startswith('#') and len(value) == 7:
                return value
            return fallback

        event = registration.event
        primary = safe_hex(getattr(event, 'primary_color', None), '#4f46e5')
        secondary = safe_hex(getattr(event, 'secondary_color', None), '#7c3aed')
        accent = safe_hex(getattr(event, 'accent_color', None), primary)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ticket_{registration.registration_number}.pdf"'

        c = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        # Background with subtle pattern
        c.setFillColor(HexColor('#f8fafc'))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        
        # Add subtle dot pattern background
        c.setFillColor(HexColor('#e5e7eb'))
        for i in range(0, int(width), 20):
            for j in range(0, int(height), 20):
                c.circle(i, j, 1, fill=1, stroke=0)

        # Main Ticket Card
        margin = 50
        card_w = 520
        card_h = 320
        card_x = (width - card_w) / 2
        card_y = (height - card_h) / 2

        # Card Shadow (outer glow effect)
        for i in range(3):
            c.setStrokeColor(HexColor('#e5e7eb'), alpha=0.3)
            c.setLineWidth(1)
            c.roundRect(card_x - i*2, card_y - i*2, card_w + i*4, card_h + i*4, 20 + i, fill=0, stroke=1)

        # Card Border/Background
        c.setStrokeColor(HexColor('#e5e7eb'))
        c.setLineWidth(1)
        c.setFillColor(white)
        c.roundRect(card_x, card_y, card_w, card_h, 20, fill=1, stroke=1)

        # LEFT SIDE (Branding & QR) - 35% width
        left_w = card_w * 0.35
        
        # Left side gradient background
        c.setFillColor(HexColor(primary))
        c.roundRect(card_x, card_y, left_w, card_h, 20, fill=1, stroke=0)
        # Cover right rounded corners to make clean edge
        c.rect(card_x + left_w - 20, card_y, 20, card_h, fill=1, stroke=0)
        
        # Background Pattern Overlay (dots)
        c.setFillColor(white, alpha=0.1)
        for i in range(int(card_x), int(card_x + left_w), 15):
            for j in range(int(card_y), int(card_y + card_h), 15):
                c.circle(i + 5, j + 5, 1.5, fill=1, stroke=0)

        # Logo Watermark on left side
        if event.logo:
            try:
                logo_path = event.logo.path
                logo_img = Image.open(logo_path)
                logo_buffer = BytesIO()
                logo_img.save(logo_buffer, format='PNG')
                logo_buffer.seek(0)
                logo_reader = ImageReader(logo_buffer)
                
                # Draw large faded watermark
                logo_size = 120
                logo_x = card_x + (left_w - logo_size) / 2
                logo_y = card_y + (card_h - logo_size) / 2
                
                c.saveState()
                c.setFillColor(white, alpha=0.08)
                c.drawImage(logo_reader, logo_x, logo_y, logo_size, logo_size, mask='auto')
                c.restoreState()
            except Exception:
                pass  # Silently skip if logo can't be loaded

        # EventHub Pass Badge at top
        badge_y = card_y + card_h - 45
        badge_w = 90
        badge_h = 22
        badge_x = card_x + (left_w - badge_w) / 2
        
        # Badge background (glass effect)
        c.setFillColor(white, alpha=0.2)
        c.roundRect(badge_x, badge_y, badge_w, badge_h, 11, fill=1, stroke=0)
        c.setStrokeColor(white, alpha=0.3)
        c.setLineWidth(0.5)
        c.roundRect(badge_x, badge_y, badge_w, badge_h, 11, fill=0, stroke=1)
        
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 8)
        c.drawCentredString(card_x + left_w/2, badge_y + 8, 'EVENTHUB PASS')

        # QR Code Container
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(registration.qr_code)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_image_reader = ImageReader(qr_buffer)
        
        qr_size = 110
        qr_x = card_x + (left_w - qr_size) / 2
        qr_y = card_y + (card_h / 2) - 20
        
        # QR White Background with subtle shadow
        c.setFillColor(white, alpha=0.9)
        c.roundRect(qr_x - 8, qr_y - 8, qr_size + 16, qr_size + 16, 12, fill=1, stroke=0)
        c.setStrokeColor(HexColor(primary), alpha=0.2)
        c.setLineWidth(2)
        c.roundRect(qr_x - 8, qr_y - 8, qr_size + 16, qr_size + 16, 12, fill=0, stroke=1)
        
        c.drawImage(qr_image_reader, qr_x, qr_y, qr_size, qr_size)

        # Ticket ID below QR
        ticket_id_y = qr_y - 25
        c.setFillColor(white, alpha=0.8)
        c.setFont('Helvetica-Bold', 7)
        c.drawCentredString(card_x + left_w/2, ticket_id_y, 'TICKET ID')
        
        c.setFillColor(white)
        c.setFont('Courier-Bold', 10)
        c.drawCentredString(card_x + left_w/2, ticket_id_y - 14, registration.registration_number)

        # Status Badge at bottom of left side
        status_y = card_y + 30
        status_w = 80
        status_h = 20
        status_x = card_x + (left_w - status_w) / 2
        
        # Status indicator (green pulsing effect simulation)
        c.setFillColor(HexColor('#22c55e'), alpha=0.3)
        c.roundRect(status_x - 2, status_y - 2, status_w + 4, status_h + 4, 10, fill=1, stroke=0)
        c.setFillColor(HexColor('#22c55e'), alpha=0.5)
        c.roundRect(status_x, status_y, status_w, status_h, 9, fill=1, stroke=0)
        
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 8)
        status_text = registration.get_status_display().upper()
        c.drawCentredString(card_x + left_w/2, status_y + 7, status_text)

        # Decorative blur circles on left side
        c.setFillColor(white, alpha=0.1)
        c.circle(card_x - 30, card_y - 30, 80, fill=1, stroke=0)
        c.circle(card_x + left_w + 30, card_y + card_h + 30, 60, fill=1, stroke=0)

        # RIGHT SIDE (Details)
        right_x = card_x + left_w + 30
        right_w = card_w - left_w - 50
        
        # Perforation line (dashed)
        c.setDash(4, 4)
        c.setStrokeColor(HexColor('#e5e7eb'))
        c.setLineWidth(1.5)
        c.line(card_x + left_w, card_y + 30, card_x + left_w, card_y + card_h - 30)
        c.setDash(1, 0)

        # Header Row: Category Badge and Event Logo
        header_y = card_y + card_h - 50
        
        # Category Badge
        cat = registration.ticket_type.ticket_category.upper() if registration.ticket_type and registration.ticket_type.ticket_category else "GENERAL"
        badge_w = 95
        badge_h = 22
        
        # Badge with colored background
        c.setFillColor(HexColor(primary + '20'))  # 20 = 12% opacity
        c.roundRect(right_x, header_y, badge_w, badge_h, 5, fill=1, stroke=0)
        c.setStrokeColor(HexColor(primary + '40'))
        c.setLineWidth(1)
        c.roundRect(right_x, header_y, badge_w, badge_h, 5, fill=0, stroke=1)
        
        c.setFillColor(HexColor(primary))
        c.setFont('Helvetica-Bold', 8)
        c.drawString(right_x + 8, header_y + 8, f"{cat} ACCESS")

        # Event Logo (small) next to badge
        if event.logo:
            try:
                logo_path = event.logo.path
                logo_img = Image.open(logo_path)
                logo_buffer = BytesIO()
                logo_img.save(logo_buffer, format='PNG')
                logo_buffer.seek(0)
                logo_reader = ImageReader(logo_buffer)
                c.drawImage(logo_reader, right_x + badge_w + 10, header_y + 2, 18, 18, mask='auto')
            except Exception:
                pass

        # Ticket Type Box (top right)
        type_box_w = 110
        type_box_h = 45
        type_box_x = card_x + card_w - type_box_w - 25
        type_box_y = header_y - 10
        
        # Subtle gradient box
        c.setFillColor(HexColor(primary + '10'))
        c.roundRect(type_box_x, type_box_y, type_box_w, type_box_h, 8, fill=1, stroke=0)
        c.setStrokeColor(HexColor(primary + '20'))
        c.roundRect(type_box_x, type_box_y, type_box_w, type_box_h, 8, fill=0, stroke=1)
        
        c.setFillColor(HexColor(primary))
        c.setFont('Helvetica-Bold', 7)
        c.drawCentredString(type_box_x + type_box_w/2, type_box_y + 28, 'TICKET TYPE')
        
        c.setFillColor(HexColor('#111827'))
        c.setFont('Helvetica-Bold', 11)
        ticket_type_name = registration.ticket_type.name if registration.ticket_type else "General"
        c.drawCentredString(type_box_x + type_box_w/2, type_box_y + 12, ticket_type_name[:15])

        # Event Title
        title_y = card_y + card_h - 95
        c.setFillColor(HexColor('#111827'))
        c.setFont('Helvetica-Bold', 24)
        
        # Truncate title if too long
        title = event.title.upper()
        if len(title) > 35:
            title = title[:32] + '...'
        c.drawString(right_x, title_y, title)

        # Info Grid with Icon Boxes
        def draw_info_section(x, y, icon_color, bg_color, icon_type, label, value, subvalue=None):
            # Icon box background
            c.setFillColor(HexColor(bg_color))
            c.roundRect(x, y - 35, 35, 35, 8, fill=1, stroke=0)
            
            # Draw simple icon representation
            c.setStrokeColor(white)
            c.setLineWidth(1.5)
            if icon_type == 'user':
                # Person icon
                c.circle(x + 17.5, y - 15, 5, stroke=1, fill=0)
                c.arc(x + 10, y - 28, x + 25, y - 18, 0, 180)
            elif icon_type == 'date':
                # Calendar icon
                c.roundRect(x + 10, y - 28, 15, 15, 2, stroke=1, fill=0)
                c.line(x + 10, y - 20, x + 25, y - 20)
                c.line(x + 13, y - 16, x + 13, y - 20)
                c.line(x + 22, y - 16, x + 22, y - 20)
            elif icon_type == 'location':
                # Location pin
                c.circle(x + 17.5, y - 16, 6, stroke=1, fill=0)
                c.line(x + 17.5, y - 22, x + 17.5, y - 30)
                c.circle(x + 17.5, y - 16, 2, stroke=0, fill=1)
            
            # Label
            text_x = x + 45
            c.setFillColor(HexColor('#9ca3af'))
            c.setFont('Helvetica-Bold', 7)
            c.drawString(text_x, y - 12, label)
            
            # Value
            c.setFillColor(HexColor('#111827'))
            c.setFont('Helvetica-Bold', 13)
            c.drawString(text_x, y - 26, value)
            
            # Subvalue (optional)
            if subvalue:
                c.setFillColor(HexColor('#6b7280'))
                c.setFont('Helvetica', 9)
                c.drawString(text_x, y - 40, subvalue)

        # Attendee Section
        attendee_y = card_y + card_h - 140
        draw_info_section(right_x, attendee_y, primary, primary + '15', 'user', 
                         'ATTENDEE', registration.attendee_name, registration.attendee_email)

        # Date & Time Section
        date_y = card_y + card_h - 140
        date_x = right_x + 180
        date_str = event.start_date.strftime('%b %d, %Y')
        time_str = event.start_date.strftime('%I:%M %p EST')
        draw_info_section(date_x, date_y, accent, accent + '15', 'date',
                         'DATE & TIME', date_str, time_str)

        # Location Section (full width)
        loc_y = card_y + card_h - 210
        draw_info_section(right_x, loc_y, secondary, secondary + '15', 'location',
                         'LOCATION', event.venue_name or 'Virtual Event')
        
        # Add address if available
        if event.address or event.city:
            address = f"{event.address or ''} {event.city or ''}, {event.country or ''}"[:50]
            c.setFillColor(HexColor('#6b7280'))
            c.setFont('Helvetica', 9)
            c.drawString(right_x + 45, loc_y - 40, address)

        # Footer
        footer_y = card_y + 25
        
        # Verified badge with checkmark
        check_x = right_x
        c.setFillColor(HexColor(primary))
        c.circle(check_x + 8, footer_y + 8, 10, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(check_x + 5, footer_y + 5, '✓')
        
        # Footer text
        c.setFillColor(HexColor(primary))
        c.setFont('Helvetica-Bold', 8)
        c.drawString(check_x + 22, footer_y + 10, 'VERIFIED EVENTHUB DIGITAL PASS')
        
        c.setFillColor(HexColor('#d1d5db'))
        c.setFont('Helvetica-Oblique', 7)
        c.drawString(check_x + 22, footer_y - 2, 'Secured & Authenticated')
        
        # Instructions on right
        c.setFillColor(HexColor('#9ca3af'))
        c.setFont('Helvetica-Oblique', 7)
        c.drawRightString(card_x + card_w - 25, footer_y + 4, 
                         'Present at registration desk for check-in')

        c.showPage()
        c.save()
        return response

    except ImportError as e:
        messages.error(request, 'PDF generation requires reportlab and pillow. Please install them.')
        return redirect('attendee:ticket_preview', registration_id=registration_id)
    except Exception as e:
        print(f"PDF Error: {str(e)}")
        messages.error(request, f"Could not generate PDF. Please try printing from the browser instead.")
        return redirect('attendee:ticket_preview', registration_id=registration_id)

    except ImportError:
        messages.error(request, 'PDF generation is not available. Please install reportlab.')
        return redirect('attendee:registration_detail', registration_id=registration.id)


@login_required
def ticket_preview(request, registration_id):
    """Preview ticket before downloading"""
    registration = get_object_or_404(
        Registration.objects.select_related('event', 'ticket_type'),
        id=registration_id
    )

    # Check permission (Allow if user is purchaser OR attendee)
    is_purchaser = registration.purchaser == request.user
    is_attendee = registration.user == request.user or registration.attendee_email.lower() == request.user.email.lower()
    
    if not (is_purchaser or is_attendee):
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('attendee:dashboard')

    qr_code_image = registration.generate_qr_code_image()

    context = {
        'registration': registration,
        'qr_code_image': qr_code_image,
    }
    return render(request, 'participant/ticket_preview.html', context)


# =============================================================================
# PRIORITY 2: Enhanced Event Discovery
# =============================================================================

def event_search(request):
    """Advanced event search with filters"""
    now = timezone.now()
    
    # Base queryset - only published and future events
    events = Event.objects.filter(
        status='published',
        start_date__gte=now
    ).order_by('start_date')
    
    # Event type filter
    event_type = request.GET.get('type')
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        events = events.filter(start_date__gte=date_from)
    if date_to:
        events = events.filter(start_date__lte=date_to)
    
    # Price range filter
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min or price_max:
        # Filter by ticket prices
        from .models import TicketType
        ticket_events = TicketType.objects.filter(is_active=True)
        if price_min:
            ticket_events = ticket_events.filter(price__gte=price_min)
        if price_max:
            ticket_events = ticket_events.filter(price__lte=price_max)
        event_ids = ticket_events.values_list('event_id', flat=True).distinct()
        events = events.filter(id__in=event_ids)
    
    # Location filter
    location = request.GET.get('location')
    if location:
        events = events.filter(
            models.Q(city__icontains=location) |
            models.Q(venue_name__icontains=location)
        )
    
    # Search query
    search_query = request.GET.get('search', '')
    if search_query:
        events = events.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    # Sort
    sort_by = request.GET.get('sort', 'date')
    if sort_by == 'date':
        events = events.order_by('start_date')
    elif sort_by == 'price_low':
        # This would need a more complex query
        pass
    elif sort_by == 'popularity':
        events = events.annotate(
            reg_count=models.Count('registrations')
        ).order_by('-reg_count')
    
    # Pagination
    paginator = Paginator(events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'event_type': event_type,
        'location': location,
        'sort_by': sort_by,
    }
    
    return render(request, 'participant/event_search.html', context)


def event_detail_enhanced(request, event_id):
    """Enhanced event detail page"""
    event = get_object_or_404(Event, id=event_id, status='published')
    
    # Get sessions preview
    sessions = event.sessions.all().order_by('start_time')[:5]
    
    # Get featured speakers
    speakers = event.speakers.filter(is_confirmed=True, is_featured=True)[:4]

    # Get dynamic sessions for the new schedule section
    dynamic_sessions = event.dynamic_sessions.all().prefetch_related('session_speakers').order_by('created_at')

    
    # Get attendee count
    attendee_count = Registration.objects.filter(
        event=event,
        status__in=[
            RegistrationStatus.PENDING,
            RegistrationStatus.CONFIRMED,
            RegistrationStatus.CHECKED_IN,
        ]
    ).count()
    has_capacity = event.max_attendees is not None
    available_spots = None
    if has_capacity:
        available_spots = max(0, event.max_attendees - attendee_count)
    
    # Get ticket types
    all_ticket_types = event.ticket_types.all()
    ticket_types = all_ticket_types.filter(is_active=True)
    now = timezone.now()
    sold_counts = {
        row['ticket_type']: row['count']
        for row in Registration.objects.filter(
            event=event,
            ticket_type__in=ticket_types,
            status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
        ).values('ticket_type').annotate(count=models.Count('id'))
    }
    available_ticket_types = []
    for ticket in ticket_types:
        # Use the dynamic properties from the model
        ticket.computed_sold = ticket.quantity_sold
        ticket.computed_available = ticket.remaining_tickets
        ticket.computed_sold_out = ticket.is_sold_out
        
        ticket.on_sale = ticket.can_purchase()
        
        if ticket.is_active:
            available_ticket_types.append(ticket)
    
    # Check if user is registered
    is_registered = False
    user_registration = None
    if request.user.is_authenticated:
        user_registration = Registration.objects.filter(
            models.Q(user=request.user) | models.Q(attendee_email__iexact=request.user.email)
        ).filter(
            event=event,
            status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
        ).first()
        is_registered = user_registration is not None
    
    # Check if event is saved
    is_saved = False
    if request.user.is_authenticated:
        # Check in user's saved events (would need a SavedEvent model)
        pass
    
    # Get similar events
    similar_events = Event.objects.filter(
        status='published',
        start_date__gte=timezone.now()
    ).exclude(id=event.id).order_by('start_date')[:3]
    
    context = {
        'event': event,
        'sessions': sessions,
        'dynamic_sessions': dynamic_sessions,
        'speakers': speakers,
        'attendee_count': attendee_count,

        'ticket_types': available_ticket_types,
        'has_ticket_types': all_ticket_types.exists(),
        'is_registered': is_registered,
        'user_registration': user_registration,
        'is_saved': is_saved,
        'similar_events': similar_events,
        'has_capacity': has_capacity,
        'available_spots': available_spots,
    }
    
    return render(request, 'participant/event_detail_enhanced.html', context)


@login_required
def save_event(request, event_id):
    """Save/unsave an event to favorites"""
    event = get_object_or_404(Event, id=event_id)
    
    # This would use a SavedEvent model (to be created)
    # For now, store in user's notification_preferences JSON field
    user = request.user
    saved_events = user.notification_preferences.get('saved_events', [])
    
    if event_id in saved_events:
        saved_events.remove(event_id)
        messages.success(request, f'Removed "{event.title}" from saved events.')
    else:
        saved_events.append(event_id)
        messages.success(request, f'Saved "{event.title}" to your favorites.')
    
    user.notification_preferences['saved_events'] = saved_events
    user.save()
    
    return redirect('attendee:event_detail', event_id=event_id)


@login_required
def saved_events(request):
    """View all saved events"""
    user = request.user
    saved_event_ids = user.notification_preferences.get('saved_events', [])
    
    events = Event.objects.filter(
        id__in=saved_event_ids,
        status='published'
    ).order_by('start_date')
    
    context = {
        'events': events,
    }
    
    return render(request, 'participant/saved_events.html', context)



# =============================================================================
# PRIORITY 3: Personal Schedule & Session Management
# =============================================================================

@login_required
def my_schedule(request):
    """View personal schedule across all events"""
    user = request.user
    now = timezone.now()
    
    # Get upcoming registrations
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        event__start_date__gte=now,
        status__in=[RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')
    
    # Get saved sessions for each event
    schedule_items = []
    for reg in registrations:
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions,
                event=reg.event
            ).order_by('start_time')
            for session in sessions:
                schedule_items.append({
                    'registration': reg,
                    'session': session,
                    'event': reg.event,
                })
    
    # Sort by start time
    schedule_items.sort(key=lambda x: x['session'].start_time)
    
    # Detect conflicts
    conflicts = []
    for i, item in enumerate(schedule_items):
        for j, other in enumerate(schedule_items[i+1:], i+1):
            if item['session'].start_time < other['session'].end_time and \
               item['session'].end_time > other['session'].start_time:
                conflicts.append((i, j))
    
    context = {
        'schedule_items': schedule_items,
        'conflicts': conflicts,
    }
    
    return render(request, 'participant/my_schedule.html', context)


@login_required
def event_schedule(request, event_id):
    """View schedule for a specific event"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    
    # Check if user is registered
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
    ).filter(
        event=event,
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        messages.error(request, 'You must be registered for this event to view the schedule.')
        return redirect('attendee:event_detail', event_id=event_id)
    
    # Get all sessions
    sessions = event.dynamic_sessions.all().prefetch_related('session_speakers').order_by('session_start_time')
    
    # Get user's saved sessions
    prefs = AttendeePreference.objects.filter(user=user, event=event).first()
    saved_session_ids = prefs.saved_sessions if prefs else []
    
    # Get tracks
    tracks = event.tracks.all()
    
    # Group sessions by day
    sessions_by_day = {}
    for session in sessions:
        if session.session_start_time:
            day = session.session_start_time.date()
            if day not in sessions_by_day:
                sessions_by_day[day] = []
            sessions_by_day[day].append(session)

    
    context = {
        'event': event,
        'registration': registration,
        'sessions': sessions,
        'sessions_by_day': sessions_by_day,
        'tracks': tracks,
        'saved_session_ids': saved_session_ids,
    }
    
    return render(request, 'participant/event_schedule.html', context)


@login_required
def save_session(request, session_id):
    """Save/unsave a session to personal schedule"""
    session = get_object_or_404(EventSession, id=session_id)
    user = request.user
    
    # Check if user is registered for the event
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
    ).filter(
        event=session.event,
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        return JsonResponse({'success': False, 'message': 'You must be registered for this event.'})
    
    # Get or create preferences
    prefs, created = AttendeePreference.objects.get_or_create(
        user=user,
        event=session.event,
        defaults={'saved_sessions': []}
    )
    
    # Toggle session
    saved_sessions = prefs.saved_sessions or []
    if session_id in saved_sessions:
        saved_sessions.remove(session_id)
        action = 'removed'
    else:
        saved_sessions.append(session_id)
        action = 'added'
    
    prefs.saved_sessions = saved_sessions
    prefs.save()
    
    return JsonResponse({
        'success': True,
        'action': action,
        'session_id': session_id
    })


@login_required
def session_feedback_enhanced(request, session_id):
    """Submit enhanced feedback for a session"""
    session = get_object_or_404(EventSession, id=session_id)
    user = request.user
    
    # Get user's registration
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
    ).filter(
        event=session.event,
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        messages.error(request, 'You must be registered for this event.')
        return redirect('attendee:event_detail', event_id=session.event.id)
    
    # Get or create attendance
    attendance, created = SessionAttendance.objects.get_or_create(
        registration=registration,
        session=session
    )
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        feedback = request.POST.get('feedback', '')
        
        if rating:
            attendance.rating = int(rating)
            attendance.feedback = feedback
            attendance.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('attendee:event_schedule', event_id=session.event.id)
    
    context = {
        'session': session,
        'attendance': attendance,
        'registration': registration,
    }
    
    return render(request, 'participant/session_feedback.html', context)


# =============================================================================
# PRIORITY 4: Networking & Communication
# =============================================================================

@login_required
def networking_hub(request):
    """Networking hub - overview of networking features"""
    user = request.user
    
    # Get user's upcoming events
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        event__start_date__gte=timezone.now(),
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')
    
    # Get recent messages
    recent_messages = AttendeeMessage.objects.filter(
        recipient=user
    ).select_related('sender', 'event').order_by('-created_at')[:5]
    
    # Get unread count
    unread_count = AttendeeMessage.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    context = {
        'registrations': registrations,
        'recent_messages': recent_messages,
        'unread_count': unread_count,
    }
    
    return render(request, 'participant/networking_hub.html', context)


@login_required
def browse_attendees(request):
    """Browse other attendees for networking"""
    user = request.user
    search_query = request.GET.get('search', '').strip()
    event_id_raw = request.GET.get('event', '').strip()
    now = timezone.now()

    # Events the user is registered for (by purchaser, user or email)
    user_regs = Registration.objects.filter(
        models.Q(purchaser=user) | models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    )
    common_events = Event.objects.filter(
        registrations__in=user_regs
    ).distinct().order_by('start_date')
    # Include ongoing events (end_date in future) and upcoming events
    common_events = common_events.filter(
        models.Q(end_date__gte=now) | models.Q(start_date__gte=now)
    )

    event_filter_id = None
    if event_id_raw:
        try:
            event_filter_id = int(event_id_raw)
        except ValueError:
            event_filter_id = None

    event_ids = list(common_events.values_list('id', flat=True))
    if event_filter_id and event_filter_id in event_ids:
        filtered_event_ids = [event_filter_id]
    else:
        filtered_event_ids = event_ids

    if not filtered_event_ids:
        attendee_qs = User.objects.none()
    else:
        attendee_qs = User.objects.filter(
            registrations__event_id__in=filtered_event_ids
        ).exclude(id=user.id).distinct()

        attendee_qs = attendee_qs.filter(
            models.Q(attendee_preferences__event_id__in=filtered_event_ids, attendee_preferences__networking_enabled=True) |
            models.Q(attendee_preferences__isnull=True)
        ).distinct()

    if search_query:
        attendee_qs = attendee_qs.filter(
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(company__icontains=search_query) |
            models.Q(job_title__icontains=search_query)
        )

    paginator = Paginator(attendee_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'common_events': common_events,
        'search_query': search_query,
    }

    return render(request, 'participant/browse_attendees.html', context)


@login_required
def attendee_profile(request, user_id):
    """View another attendee's public profile"""
    profile_user = get_object_or_404(User, id=user_id)
    
    common_events = Event.objects.filter(
        registrations__purchaser=request.user
    ).filter(
        registrations__user=profile_user
    ).distinct()

    connection_messages = AttendeeMessage.objects.filter(
        models.Q(sender=request.user, recipient=profile_user) |
        models.Q(sender=profile_user, recipient=request.user)
    )

    connection_status = 'none'
    if connection_messages.exists():
        pending_request = connection_messages.filter(
            sender=request.user,
            recipient=profile_user,
            subject__iexact='Connection Request'
        ).exists()
        if pending_request and not connection_messages.filter(sender=profile_user, recipient=request.user).exists():
            connection_status = 'pending'
        else:
            connection_status = 'connected'

    # Normalize twitter url for template usage
    if getattr(profile_user, 'twitter_handle', ''):
        handle = profile_user.twitter_handle.strip()
        if handle and not handle.startswith('http'):
            handle = handle.lstrip('@')
            profile_user.twitter_url = f"https://twitter.com/{handle}"
        else:
            profile_user.twitter_url = handle
    
    context = {
        'profile_user': profile_user,
        'common_events': common_events,
        'connection_status': connection_status,
    }
    
    return render(request, 'participant/attendee_profile.html', context)


@login_required
def send_connection_request(request, user_id):
    """Send a connection request / message to another attendee"""
    recipient = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        message_text = request.POST.get('message', '')
        
        event = None
        if event_id:
            event = get_object_or_404(Event, id=event_id)
        
        # Create message
        AttendeeMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            event=event,
            subject='Connection Request',
            message=message_text
        )
        
        messages.success(request, f'Connection request sent to {recipient.email}')
        return redirect('attendee:networking_hub')
    
    # Get common events
    common_events = Event.objects.filter(
        registrations__purchaser=request.user
    ).filter(
        registrations__user=recipient
    ).distinct()
    
    context = {
        'recipient': recipient,
        'common_events': common_events,
    }
    
    return render(request, 'participant/send_connection_request.html', context)


@login_required
def messages_enhanced(request):
    """Enhanced threaded messaging interface"""
    user = request.user
    
    # Get all messages where user is sender or recipient
    all_messages = AttendeeMessage.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related('sender', 'recipient', 'event').order_by('-created_at')
    
    # Group into threads (by other user)
    threads = {}
    for msg in all_messages:
        other_user = msg.recipient if msg.sender == user else msg.sender
        if other_user.id not in threads:
            threads[other_user.id] = {
                'user': other_user,
                'last_message': msg,
                'unread_count': 0
            }
        if not msg.is_read and msg.recipient == user:
            threads[other_user.id]['unread_count'] += 1
            
    threads_data = list(threads.values())
    
    # Selected thread
    selected_thread_id = request.GET.get('thread')
    selected_thread = None
    thread_messages = []
    
    if selected_thread_id:
        selected_thread = get_object_or_404(User, id=selected_thread_id)
        # Get conversation between user and selected_thread
        thread_messages = AttendeeMessage.objects.filter(
            (Q(sender=user) & Q(recipient=selected_thread)) |
            (Q(sender=selected_thread) & Q(recipient=user))
        ).order_by('created_at')
        
        # Mark as read
        AttendeeMessage.objects.filter(
            sender=selected_thread,
            recipient=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
    
    context = {
        'threads_data': threads_data,
        'selected_thread': selected_thread,
        'thread_messages': thread_messages,
        'unread_count': sum(t['unread_count'] for t in threads_data),
    }
    
    return render(request, 'participant/messages_enhanced.html', context)


@login_required
def send_message_enhanced(request, recipient_id):
    """Send a message to another attendee"""
    recipient = get_object_or_404(User, id=recipient_id)
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        message_text = request.POST.get('message', '')
        event_id = request.POST.get('event_id')
        
        event = None
        if event_id:
            event = get_object_or_404(Event, id=event_id)
        
        AttendeeMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            event=event,
            subject=subject,
            message=message_text
        )
        
        messages.success(request, f'Message sent to {recipient.email}')
        
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
            
        return redirect('attendee:messages')
    
    # Get common events
    common_events = Event.objects.filter(
        registrations__purchaser=request.user
    ).filter(
        registrations__user=recipient
    ).distinct()
    
    context = {
        'recipient': recipient,
        'common_events': common_events,
    }
    
    return render(request, 'participant/send_message.html', context)


@login_required
def mark_message_read_enhanced(request, message_id):
    """Mark a message as read"""
    message = get_object_or_404(AttendeeMessage, id=message_id, recipient=request.user)
    
    if not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
    
    return redirect('attendee:messages')


# =============================================================================
# PRIORITY 5: Preferences & Settings
# =============================================================================

@login_required
def preferences_enhanced(request, event_id):
    """Enhanced preferences management for an event"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    
    # Check if user is registered
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
    ).filter(
        event=event,
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        messages.error(request, 'You must be registered for this event.')
        return redirect('attendee:event_detail', event_id=event_id)
    
    # Get or create preferences
    prefs, created = AttendeePreference.objects.get_or_create(
        user=user,
        event=event,
        defaults={}
    )
    
    if request.method == 'POST':
        # Update preferences
        prefs.interested_topics = request.POST.getlist('interested_topics', [])
        prefs.preferred_tracks = request.POST.getlist('preferred_tracks', [])
        prefs.dietary_requirements = request.POST.getlist('dietary_requirements', [])
        prefs.dietary_notes = request.POST.get('dietary_notes', '')
        prefs.accessibility_needs = request.POST.getlist('accessibility_needs', [])
        prefs.accessibility_notes = request.POST.get('accessibility_notes', '')
        prefs.networking_enabled = 'networking_enabled' in request.POST
        prefs.networking_bio = request.POST.get('networking_bio', '')
        prefs.linkedin_url = request.POST.get('linkedin_url', '')
        prefs.twitter_handle = request.POST.get('twitter_handle', '')
        prefs.email_notifications = 'email_notifications' in request.POST
        prefs.sms_notifications = 'sms_notifications' in request.POST
        prefs.save()
        
        messages.success(request, 'Preferences saved successfully!')
        return redirect('attendee:registration_detail', registration_id=registration.id)
    
    # Get tracks for selection
    tracks = event.tracks.all()
    
    context = {
        'event': event,
        'registration': registration,
        'preferences': prefs,
        'tracks': tracks,
    }
    
    return render(request, 'participant/preferences.html', context)


@login_required
def account_settings(request):
    """Account settings page"""
    user = request.user
    
    if request.method == 'POST':
        # Update user profile
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.company = request.POST.get('company', '')
        user.job_title = request.POST.get('job_title', '')
        user.bio = request.POST.get('bio', '')
        user.linkedin_url = request.POST.get('linkedin_url', '')
        user.twitter_handle = request.POST.get('twitter_handle', '')
        user.website = request.POST.get('website', '')
        
        # Handle profile image upload
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        
        user.save()
        messages.success(request, 'Settings saved successfully!')
        return redirect('attendee:settings')
    
    context = {
        'user': user,
    }
    
    return render(request, 'participant/account_settings.html', context)


# =============================================================================
# PRIORITY 6: Check-In & Badge Management
# =============================================================================

@login_required
def my_tickets(request):
    """Display all purchased tickets including upcoming and past events.
    Shows tickets where user is attendee, purchaser, or email matches.
    Excludes waitlisted registrations (those without actual tickets)."""
    user = request.user
    now = timezone.now()

    # Get all confirmed/checked-in/pending registrations for this user that have tickets
    # Include tickets where user is purchaser (bought for others) or attendee
    # Exclude waitlisted registrations (those without tickets)
    all_registrations = Registration.objects.filter(
        models.Q(user=user) | 
        models.Q(attendee_email__iexact=user.email) |
        models.Q(purchaser=user),  # Include tickets purchased for others
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).exclude(
        ticket_type__isnull=True  # Exclude registrations without tickets (waitlisted)
    ).select_related('event', 'ticket_type').order_by('event__start_date')

    # Separate into upcoming and past
    upcoming_registrations = all_registrations.filter(event__start_date__gte=now)
    past_registrations = all_registrations.filter(event__start_date__lt=now)

    def create_tickets_list(registrations):
        tickets = []
        for reg in registrations:
            try:
                qr_image = reg.generate_qr_code_image()
            except Exception:
                qr_image = None
            tickets.append({
                'registration': reg,
                'qr_image': qr_image,
            })
        return tickets

    upcoming_tickets = create_tickets_list(upcoming_registrations)
    past_tickets = create_tickets_list(past_registrations)

    context = {
        'upcoming_tickets': upcoming_tickets,
        'past_tickets': past_tickets,
        'has_any_tickets': all_registrations.exists(),
    }
    return render(request, 'participant/my_tickets.html', context)


@login_required
def digital_badge(request, registration_id):
    """Display digital badge with social sharing options"""
    registration = get_object_or_404(Registration, id=registration_id)

    if registration.user != request.user and registration.attendee_email.lower() != request.user.email.lower():
        messages.error(request, 'You do not have permission to view this badge.')
        return redirect('attendee:dashboard')

    badge = getattr(registration, 'badge', None)
    if not badge:
        badge = Badge.objects.create(
            registration=registration,
            name=registration.attendee_name,
            badge_type='vip' if registration.ticket_type and registration.ticket_type.ticket_category == 'vip' else 'standard',
            qr_code_data=f"BADGE:{registration.qr_code}",
        )

    try:
        qr_image = badge.generate_qr_code()
    except Exception:
        qr_image = None

    context = {
        'registration': registration,
        'badge': badge,
        'qr_image': qr_image,
    }
    return render(request, 'participant/digital_badge.html', context)


# =============================================================================
# PRIORITY 7: Post-Event Experience
# =============================================================================

@login_required
def certificates_list(request):
    """List all events where attendee has checked-in status"""
    user = request.user

    # Get registrations where the user is purchaser OR attendee
    checked_in_registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        status=RegistrationStatus.CHECKED_IN
    ).select_related('event').order_by('-event__start_date')

    context = {
        'registrations': checked_in_registrations,
    }
    return render(request, 'participant/certificates.html', context)


@login_required
def download_certificate(request, registration_id):
    """Generate and download PDF certificate"""
    registration = get_object_or_404(Registration, id=registration_id)

    if registration.user != request.user and registration.attendee_email.lower() != request.user.email.lower():
        messages.error(request, 'You do not have permission to download this certificate.')
        return redirect('attendee:certificates')

    if registration.status != RegistrationStatus.CHECKED_IN:
        messages.error(request, 'Certificate is only available for events you have checked in to.')
        return redirect('attendee:certificates')

    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate_{registration.registration_number}.pdf"'

        c = canvas.Canvas(response, pagesize=landscape(A4))
        width, height = landscape(A4)

        # Background
        c.setFillColor(HexColor('#f8f9fa'))
        c.rect(0, 0, width, height, fill=1)

        # Border
        c.setStrokeColor(HexColor('#4f46e5'))
        c.setLineWidth(4)
        c.rect(30, 30, width - 60, height - 60)
        c.setLineWidth(1)
        c.rect(40, 40, width - 80, height - 80)

        # Title
        c.setFillColor(HexColor('#4f46e5'))
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(width / 2, height - 120, "Certificate of Attendance")

        # Decorative line
        c.setStrokeColor(HexColor('#a78bfa'))
        c.setLineWidth(2)
        c.line(width / 2 - 150, height - 135, width / 2 + 150, height - 135)

        # Body text
        c.setFillColor(HexColor('#374151'))
        c.setFont("Helvetica", 16)
        c.drawCentredString(width / 2, height - 180, "This is to certify that")

        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(HexColor('#1f2937'))
        c.drawCentredString(width / 2, height - 220, registration.attendee_name)

        c.setFont("Helvetica", 16)
        c.setFillColor(HexColor('#374151'))
        c.drawCentredString(width / 2, height - 260, "has successfully attended")

        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(HexColor('#4f46e5'))
        c.drawCentredString(width / 2, height - 300, registration.event.title)

        c.setFont("Helvetica", 14)
        c.setFillColor(HexColor('#6b7280'))
        date_str = registration.event.start_date.strftime('%B %d, %Y')
        venue = registration.event.venue_name or 'Virtual Event'
        c.drawCentredString(width / 2, height - 335, f"held on {date_str} at {venue}")

        # Registration number
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor('#9ca3af'))
        c.drawCentredString(width / 2, 70, f"Certificate ID: {registration.registration_number}")

        c.save()
        return response

    except ImportError:
        messages.error(request, 'PDF generation is not available. Please install reportlab.')
        return redirect('attendee:certificates')


@login_required
def event_materials(request, event_id):
    """Access session materials for a registered event"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # Get registration where user is purchaser OR attendee
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
    ).filter(
        event=event,
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()

    if not registration:
        messages.error(request, 'You must be registered for this event to access materials.')
        return redirect('attendee:event_detail', event_id=event_id)

    sessions_with_materials = event.sessions.filter(
        models.Q(slides__isnull=False) |
        models.Q(recording_url__gt='') |
        models.Q(resources__isnull=False)
    ).exclude(
        slides='', recording_url='', resources=[]
    ).order_by('start_time')

    context = {
        'event': event,
        'registration': registration,
        'sessions': sessions_with_materials,
    }
    return render(request, 'participant/event_materials.html', context)


@login_required
def event_feedback(request, event_id):
    """Submit overall event feedback"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # Get registration where user is purchaser OR attendee
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
    ).filter(
        event=event,
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()

    if not registration:
        messages.error(request, 'You must be registered for this event to submit feedback.')
        return redirect('attendee:event_detail', event_id=event_id)

    if request.method == 'POST':
        overall_rating = request.POST.get('overall_rating')
        feedback_text = request.POST.get('feedback', '')

        registration.custom_fields['event_feedback'] = {
            'rating': int(overall_rating) if overall_rating else None,
            'feedback': feedback_text,
            'submitted_at': timezone.now().isoformat(),
        }
        registration.save()
        messages.success(request, 'Thank you for your feedback!')
        return redirect('attendee:registration_detail', registration_id=registration.id)

    existing_feedback = registration.custom_fields.get('event_feedback', {})

    context = {
        'event': event,
        'registration': registration,
        'existing_feedback': existing_feedback,
    }
    return render(request, 'participant/event_feedback.html', context)


# =============================================================================
# PRIORITY 8: Notifications
# =============================================================================

@login_required
def notifications_list(request):
    """View all notifications"""
    from .models import AttendeeNotification

    user = request.user
    filter_type = request.GET.get('filter', 'all')

    notifications = AttendeeNotification.objects.filter(user=user).order_by('-created_at')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    unread_count = AttendeeNotification.objects.filter(user=user, is_read=False).count()

    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'unread_count': unread_count,
    }
    return render(request, 'participant/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    from .models import AttendeeNotification

    notification = get_object_or_404(AttendeeNotification, id=notification_id, user=request.user)
    notification.mark_read()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('attendee:notifications')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    from .models import AttendeeNotification

    AttendeeNotification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, 'All notifications marked as read.')
    return redirect('attendee:notifications')


# =============================================================================
# PRIORITY 9: Schedule Export
# =============================================================================

@login_required
def export_schedule_ical(request):
    """Export personal schedule to iCal format"""
    user = request.user
    now = timezone.now()

    # Get registrations where user is purchaser OR attendee
    registrations = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        event__start_date__gte=now,
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).select_related('event')

    def escape_ical_text(value):
        """
        Escape text per RFC 5545 so mobile calendars can parse it reliably.
        """
        if not value:
            return ""
        text = str(value)
        text = text.replace("\\", "\\\\")
        text = text.replace(";", "\\;")
        text = text.replace(",", "\\,")
        text = text.replace("\r\n", "\\n").replace("\n", "\\n")
        return text

    cal_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//EventPortal//Schedule//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for reg in registrations:
        prefs = AttendeePreference.objects.filter(user=user, event=reg.event).first()
        if prefs and prefs.saved_sessions:
            sessions = EventSession.objects.filter(
                id__in=prefs.saved_sessions, event=reg.event
            ).order_by('start_time')
            for session in sessions:
                # Normalize to UTC and format with Z suffix
                if timezone.is_aware(session.start_time):
                    start_utc = timezone.localtime(session.start_time, timezone.utc)
                else:
                    start_utc = session.start_time
                if timezone.is_aware(session.end_time):
                    end_utc = timezone.localtime(session.end_time, timezone.utc)
                else:
                    end_utc = session.end_time

                dtstamp = timezone.now()

                cal_lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:eventhub-{session.id}-{reg.id}@eventportal",
                    f"DTSTAMP:{dtstamp.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
                    f"SUMMARY:{escape_ical_text(session.title)}",
                    f"DESCRIPTION:{escape_ical_text(session.description[:200] if session.description else '')}",
                    f"LOCATION:{escape_ical_text(session.location or reg.event.venue_name or '')}",
                    "END:VEVENT",
                ])

    cal_lines.append("END:VCALENDAR")

    response = HttpResponse('\r\n'.join(cal_lines), content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename="my_schedule.ics"'
    return response


@login_required
def add_to_google_calendar(request, session_id):
    """
    Generate Google Calendar 'Add Event' URL for a specific session.
    Redirects user to Google Calendar with pre-filled event details.
    """
    from django.urls import reverse
    
    # Get the session
    session = get_object_or_404(EventSession, id=session_id)
    event = session.event
    user = request.user
    
    # Check if user is registered for this event
    registration = Registration.objects.filter(
        models.Q(user=user) | models.Q(attendee_email__iexact=user.email),
        event=event,
        status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
    ).first()
    
    if not registration:
        messages.error(request, 'You must be registered for this event to add sessions to your calendar.')
        return redirect('attendee:my_schedule')
    
    # Format dates for Google Calendar (UTC format: YYYYMMDDTHHMMSSZ)
    start_time = session.start_time
    end_time = session.end_time
    
    if timezone.is_aware(start_time):
        start_time = timezone.localtime(start_time, timezone.utc)
    if timezone.is_aware(end_time):
        end_time = timezone.localtime(end_time, timezone.utc)
    
    start_str = start_time.strftime('%Y%m%dT%H%M%SZ')
    end_str = end_time.strftime('%Y%m%dT%H%M%SZ')
    
    # Build Google Calendar URL
    base_url = 'https://calendar.google.com/calendar/render'
    
    # Prepare event details
    title = quote(f"{event.title}: {session.title}")
    details = quote(f"Session: {session.title}\\nEvent: {event.title}\\n\\n{session.description or ''}")
    location = quote(session.location or event.venue_name or '')
    
    # Build the action=TEMPLATE URL
    google_url = (
        f"{base_url}?action=TEMPLATE"
        f"&text={title}"
        f"&dates={start_str}/{end_str}"
        f"&details={details}"
        f"&location={location}"
    )
    
    return HttpResponseRedirect(google_url)


# =============================================================================
# PROFILE AND SETTINGS VIEWS
# =============================================================================

@login_required
def attendee_profile_edit(request):
    """Enhanced profile editing view"""
    user = request.user
    
    if request.method == 'POST':
        # Handle profile updates
        try:
            # Update basic fields
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.phone = request.POST.get('phone', '').strip()
            user.company = request.POST.get('company', '').strip()
            user.job_title = request.POST.get('job_title', '').strip()
            user.bio = request.POST.get('bio', '').strip()
            user.linkedin_url = request.POST.get('linkedin_url', '').strip()
            user.website = request.POST.get('website', '').strip()
            
            # Handle profile image upload
            if 'profile_image' in request.FILES:
                user.profile_image = request.FILES['profile_image']
            
            user.save()
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
            else:
                messages.success(request, 'Profile updated successfully!')
                return redirect('attendee:profile')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error updating profile: {str(e)}')
    
    # Get profile stats
    try:
        all_registrations = Registration.objects.filter(
            models.Q(user=user) | models.Q(attendee_email__iexact=user.email)
        )
        
        now = timezone.now()
        events_attended = all_registrations.filter(
            event__end_date__lt=now,
            status=RegistrationStatus.CHECKED_IN
        ).count()
        
        upcoming_events = all_registrations.filter(
            event__start_date__gte=now,
            status__in=[RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED, RegistrationStatus.CHECKED_IN]
        ).count()
    except:
        events_attended = 0
        upcoming_events = 0
    
    # Get certificates count (placeholder)
    certificates_count = 0
    
    context = {
        'user': user,
        'events_attended': events_attended,
        'upcoming_events': upcoming_events,
        'certificates_count': certificates_count,
    }
    
    return render(request, 'participant/profile.html', context)


@login_required
def account_settings(request):
    """Account settings view with tabs for different settings categories"""
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action', 'change_password')  # Default action
        
        if action == 'change_password':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not current_password or not new_password or not confirm_password:
                return JsonResponse({'success': False, 'error': 'All password fields are required'})
            
            if not user.check_password(current_password):
                return JsonResponse({'success': False, 'error': 'Current password is incorrect'})
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'error': 'New passwords do not match'})
            
            if len(new_password) < 8:
                return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long'})
            
            try:
                user.set_password(new_password)
                user.save()
                return JsonResponse({'success': True, 'message': 'Password updated successfully!'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating password: {str(e)}'})
        
        elif action == 'update_notifications':
            # Handle notification preferences
            try:
                # Get notification preferences from form
                event_reminders = request.POST.get('event_reminders') == 'on'
                ticket_confirmations = request.POST.get('ticket_confirmations') == 'on'
                event_updates = request.POST.get('event_updates') == 'on'
                marketing_notifications = request.POST.get('marketing_notifications') == 'on'
                weekly_newsletter = request.POST.get('weekly_newsletter') == 'on'
                
                # Update user notification preferences (you can store this in user.notification_preferences JSON field)
                if not user.notification_preferences:
                    user.notification_preferences = {}
                
                user.notification_preferences.update({
                    'event_reminders': event_reminders,
                    'ticket_confirmations': ticket_confirmations,
                    'event_updates': event_updates,
                    'marketing_notifications': marketing_notifications,
                    'weekly_newsletter': weekly_newsletter,
                })
                user.save()
                
                return JsonResponse({'success': True, 'message': 'Notification preferences updated!'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating notifications: {str(e)}'})
        
        elif action == 'update_privacy':
            # Handle privacy settings
            try:
                public_profile = request.POST.get('public_profile') == 'on'
                hide_email = request.POST.get('hide_email') == 'on'
                hide_phone = request.POST.get('hide_phone') == 'on'
                analytics_sharing = request.POST.get('analytics_sharing') == 'on'
                
                # Update user privacy preferences
                if not user.notification_preferences:
                    user.notification_preferences = {}
                
                user.notification_preferences.update({
                    'public_profile': public_profile,
                    'hide_email': hide_email,
                    'hide_phone': hide_phone,
                    'analytics_sharing': analytics_sharing,
                })
                user.save()
                
                return JsonResponse({'success': True, 'message': 'Privacy settings updated!'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating privacy settings: {str(e)}'})
        
        elif action == 'update_preferences':
            # Handle general preferences
            try:
                language = request.POST.get('language', 'en')
                timezone_pref = request.POST.get('timezone', 'UTC')
                theme = request.POST.get('theme', 'light')
                email_format = request.POST.get('email_format', 'html')
                
                # Update user general preferences
                if not user.notification_preferences:
                    user.notification_preferences = {}
                
                user.notification_preferences.update({
                    'language': language,
                    'timezone': timezone_pref,
                    'theme': theme,
                    'email_format': email_format,
                })
                user.save()
                
                return JsonResponse({'success': True, 'message': 'Preferences updated!'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating preferences: {str(e)}'})
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    # Get current preferences for display
    preferences = user.notification_preferences or {}
    
    context = {
        'user': user,
        'preferences': preferences,
    }
    
    return render(request, 'participant/account_settings.html', context)
