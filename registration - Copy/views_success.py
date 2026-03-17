"""
Registration success page and QR code email functionality
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import json

from .models import Registration


def send_qr_email_direct(registration):
    """Send QR code email directly (called from registration API)"""
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    
    # Generate QR code
    qr_code_image = registration.generate_qr_code_image()
    
    # Prepare email
    subject = f'Your Event Ticket - {registration.event.title}'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = registration.attendee_email
    
    # Create HTML email content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .qr-container {{ text-align: center; margin: 30px 0; padding: 20px; background: white; border-radius: 10px; }}
            .qr-code {{ max-width: 250px; height: auto; border: 4px solid #667eea; border-radius: 10px; }}
            .details {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .detail-row {{ display: flex; padding: 10px 0; border-bottom: 1px solid #eee; }}
            .detail-label {{ font-weight: bold; width: 150px; color: #667eea; }}
            .detail-value {{ flex: 1; }}
            .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Registration Confirmed!</h1>
                <p>Your ticket for {registration.event.title}</p>
            </div>
            
            <div class="content">
                <p>Dear {registration.attendee_name},</p>
                
                <p>Thank you for registering! Your ticket has been confirmed. Please find your QR code below:</p>
                
                <div class="qr-container">
                    <img src="data:image/png;base64,{qr_code_image}" alt="QR Code" class="qr-code">
                    <p style="margin-top: 15px; color: #667eea; font-weight: bold;">Registration: {registration.registration_number}</p>
                </div>
                
                <div class="details">
                    <h3 style="color: #667eea; margin-top: 0;">Event Details</h3>
                    <div class="detail-row">
                        <span class="detail-label">Event:</span>
                        <span class="detail-value">{registration.event.title}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">{registration.event.start_date.strftime('%B %d, %Y')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">{registration.event.start_date.strftime('%I:%M %p')}</span>
                    </div>
                    {f'<div class="detail-row"><span class="detail-label">Venue:</span><span class="detail-value">{registration.event.venue_name}</span></div>' if registration.event.venue_name else ''}
                    {f'<div class="detail-row"><span class="detail-label">Ticket Type:</span><span class="detail-value">{registration.ticket_type.name}</span></div>' if registration.ticket_type else ''}
                    <div class="detail-row" style="border-bottom: none;">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value" style="color: #10b981; font-weight: bold;">{registration.get_status_display()}</span>
                    </div>
                </div>
                
                <div style="background: #e0e7ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #667eea;">📋 Important Instructions</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Save this email or take a screenshot of the QR code</li>
                        <li>Show the QR code at the event entrance for check-in</li>
                        <li>Bring a valid ID along with your ticket</li>
                        <li>Arrive at least 15 minutes before the event starts</li>
                    </ul>
                </div>
                
                <p>We look forward to seeing you at the event!</p>
                
                <p>Best regards,<br>
                <strong>Event Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated email. Please do not reply to this message.</p>
                <p>If you have any questions, contact us at support@example.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    Registration Confirmed!
    
    Dear {registration.attendee_name},
    
    Thank you for registering for {registration.event.title}!
    
    Registration Number: {registration.registration_number}
    Event: {registration.event.title}
    Date: {registration.event.start_date.strftime('%B %d, %Y')}
    Time: {registration.event.start_date.strftime('%I:%M %p')}
    {f'Venue: {registration.event.venue_name}' if registration.event.venue_name else ''}
    {f'Ticket Type: {registration.ticket_type.name}' if registration.ticket_type else ''}
    Status: {registration.get_status_display()}
    
    Important Instructions:
    - Save this email or take a screenshot of the QR code
    - Show the QR code at the event entrance for check-in
    - Bring a valid ID along with your ticket
    - Arrive at least 15 minutes before the event starts
    
    We look forward to seeing you at the event!
    
    Best regards,
    Event Team
    """
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    
    # Send email
    email.send(fail_silently=False)


def registration_success(request, registration_id):
    """Display registration success page with QR code"""
    registration = get_object_or_404(Registration, id=registration_id)
    
    # Generate QR code image
    qr_code_image = registration.generate_qr_code_image()
    
    context = {
        'registration': registration,
        'event': registration.event,
        'qr_code_image': qr_code_image,
    }
    
    return render(request, 'participant/registration_success.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def send_qr_email(request):
    """Send QR code via email to registered participant"""
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')
        
        if not registration_id:
            return JsonResponse({'success': False, 'message': 'Registration ID required'}, status=400)
        
        registration = get_object_or_404(Registration, id=registration_id)
        
        # Generate QR code
        qr_code_image = registration.generate_qr_code_image()
        
        # Prepare email
        subject = f'Your Event Ticket - {registration.event.title}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = registration.attendee_email
        
        # Create HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .qr-container {{ text-align: center; margin: 30px 0; padding: 20px; background: white; border-radius: 10px; }}
                .qr-code {{ max-width: 250px; height: auto; border: 4px solid #667eea; border-radius: 10px; }}
                .details {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .detail-row {{ display: flex; padding: 10px 0; border-bottom: 1px solid #eee; }}
                .detail-label {{ font-weight: bold; width: 150px; color: #667eea; }}
                .detail-value {{ flex: 1; }}
                .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 12px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Registration Confirmed!</h1>
                    <p>Your ticket for {registration.event.title}</p>
                </div>
                
                <div class="content">
                    <p>Dear {registration.attendee_name},</p>
                    
                    <p>Thank you for registering! Your ticket has been confirmed. Please find your QR code below:</p>
                    
                    <div class="qr-container">
                        <img src="data:image/png;base64,{qr_code_image}" alt="QR Code" class="qr-code">
                        <p style="margin-top: 15px; color: #667eea; font-weight: bold;">Registration: {registration.registration_number}</p>
                    </div>
                    
                    <div class="details">
                        <h3 style="color: #667eea; margin-top: 0;">Event Details</h3>
                        <div class="detail-row">
                            <span class="detail-label">Event:</span>
                            <span class="detail-value">{registration.event.title}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Date:</span>
                            <span class="detail-value">{registration.event.start_date.strftime('%B %d, %Y')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Time:</span>
                            <span class="detail-value">{registration.event.start_date.strftime('%I:%M %p')}</span>
                        </div>
                        {f'<div class="detail-row"><span class="detail-label">Venue:</span><span class="detail-value">{registration.event.venue_name}</span></div>' if registration.event.venue_name else ''}
                        {f'<div class="detail-row"><span class="detail-label">Ticket Type:</span><span class="detail-value">{registration.ticket_type.name}</span></div>' if registration.ticket_type else ''}
                        <div class="detail-row" style="border-bottom: none;">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value" style="color: #10b981; font-weight: bold;">{registration.get_status_display()}</span>
                        </div>
                    </div>
                    
                    <div style="background: #e0e7ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h4 style="margin-top: 0; color: #667eea;">📋 Important Instructions</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Save this email or take a screenshot of the QR code</li>
                            <li>Show the QR code at the event entrance for check-in</li>
                            <li>Bring a valid ID along with your ticket</li>
                            <li>Arrive at least 15 minutes before the event starts</li>
                        </ul>
                    </div>
                    
                    <p>We look forward to seeing you at the event!</p>
                    
                    <p>Best regards,<br>
                    <strong>Event Team</strong></p>
                </div>
                
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                    <p>If you have any questions, contact us at support@example.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Registration Confirmed!
        
        Dear {registration.attendee_name},
        
        Thank you for registering for {registration.event.title}!
        
        Registration Number: {registration.registration_number}
        Event: {registration.event.title}
        Date: {registration.event.start_date.strftime('%B %d, %Y')}
        Time: {registration.event.start_date.strftime('%I:%M %p')}
        {f'Venue: {registration.event.venue_name}' if registration.event.venue_name else ''}
        {f'Ticket Type: {registration.ticket_type.name}' if registration.ticket_type else ''}
        Status: {registration.get_status_display()}
        
        Important Instructions:
        - Save this email or take a screenshot of the QR code
        - Show the QR code at the event entrance for check-in
        - Bring a valid ID along with your ticket
        - Arrive at least 15 minutes before the event starts
        
        We look forward to seeing you at the event!
        
        Best regards,
        Event Team
        """
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        return JsonResponse({
            'success': True,
            'message': 'Email sent successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def send_no_ticket_notification(registration):
    """Send notification for events without tickets (waitlist/interest)"""
    from .models import AttendeeNotification
    
    # 1. System Notification
    AttendeeNotification.objects.create(
        user=registration.user,
        notification_type='event_update',
        title=f"Registration Received: {registration.event.title}",
        message=f"Thank you for registering for {registration.event.title}. We will notify you as soon as tickets become available.",
        related_event=registration.event,
        link=f"/attendee/registration/{registration.id}/"
    )
    
    # 2. Email Notification
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    
    subject = f"Registration Received: {registration.event.title}"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = registration.attendee_email
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .info-box {{ background: #fffbeb; border: 1px solid #fef3c7; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⏳ Registration Received</h1>
                <p>{registration.event.title}</p>
            </div>
            <div class="content">
                <p>Dear {registration.attendee_name},</p>
                <p>Thank you for your interest in <strong>{registration.event.title}</strong>!</p>
                <div class="info-box">
                    <h3 style="color: #d97706; margin-top: 0;">What's Next?</h3>
                    <p>We've received your registration. Since tickets are not yet available for this event, we've added you to our interest list.</p>
                    <p><strong>We will notify you immediately via email as soon as tickets become available for purchase.</strong></p>
                </div>
                <p><strong>Registration Number:</strong> {registration.registration_number}</p>
                <p>Best regards,<br><strong>Event Team</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"Thank you for registering for {registration.event.title}. We will notify you as soon as tickets become available."
    
    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)
