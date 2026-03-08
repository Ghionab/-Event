from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import (
    EmailTemplate, EmailLog, ScheduledEmail, SMSNotification,
    PushNotification, LivePoll, PollResponse, LiveQA, AutomatedReminder
)
from .forms import EmailTemplateForm, ScheduledEmailForm, LivePollForm, LiveQAForm
from events.models import Event
from registration.models import Registration


# ============ Email Management ============

@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def email_templates(request):
    """List all email templates"""
    templates = EmailTemplate.objects.all()
    return render(request, 'communication/email_templates.html', {'templates': templates})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def email_template_create(request):
    """Create a new email template"""
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email template created successfully!')
            return redirect('communication:email_templates')
    else:
        form = EmailTemplateForm()
    
    return render(request, 'communication/email_template_form.html', {'form': form})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def email_template_edit(request, template_id):
    """Edit an email template"""
    template = get_object_or_404(EmailTemplate, id=template_id)
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email template updated successfully!')
            return redirect('communication:email_templates')
    else:
        form = EmailTemplateForm(instance=template)
    
    return render(request, 'communication/email_template_form.html', {'form': form, 'template': template})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def email_template_delete(request, template_id):
    """Delete an email template"""
    template = get_object_or_404(EmailTemplate, id=template_id)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Email template deleted successfully!')
        return redirect('communication:email_templates')
    
    return render(request, 'communication/confirm_delete.html', {'object': template})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def email_logs(request):
    """View email sending logs"""
    logs = EmailLog.objects.all()[:100]
    return render(request, 'communication/email_logs.html', {'logs': logs})


# ============ Scheduled Emails ============

@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def scheduled_emails(request):
    """List scheduled emails"""
    scheduled = ScheduledEmail.objects.all()
    return render(request, 'communication/scheduled_emails.html', {'scheduled': scheduled})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def scheduled_email_create(request):
    """Create a scheduled email"""
    if request.method == 'POST':
        form = ScheduledEmailForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Scheduled email created successfully!')
            return redirect('communication:scheduled_emails')
    else:
        form = ScheduledEmailForm()
    
    return render(request, 'communication/scheduled_email_form.html', {'form': form})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def scheduled_email_edit(request, scheduled_id):
    """Edit a scheduled email"""
    scheduled = get_object_or_404(ScheduledEmail, id=scheduled_id)
    
    if request.method == 'POST':
        form = ScheduledEmailForm(request.POST, instance=scheduled)
        if form.is_valid():
            form.save()
            messages.success(request, 'Scheduled email updated successfully!')
            return redirect('communication:scheduled_emails')
    else:
        form = ScheduledEmailForm(instance=scheduled)
    
    return render(request, 'communication/scheduled_email_form.html', {'form': form, 'scheduled': scheduled})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def scheduled_email_delete(request, scheduled_id):
    """Delete a scheduled email"""
    scheduled = get_object_or_404(ScheduledEmail, id=scheduled_id)
    
    if request.method == 'POST':
        scheduled.delete()
        messages.success(request, 'Scheduled email deleted successfully!')
        return redirect('communication:scheduled_emails')
    
    return render(request, 'communication/confirm_delete.html', {'object': scheduled})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def send_scheduled_email(request, scheduled_id):
    """Send a scheduled email immediately"""
    scheduled = get_object_or_404(ScheduledEmail, id=scheduled_id)
    
    # Get recipients based on filter
    recipients = get_recipients_for_filter(scheduled.event, scheduled.recipient_filter)
    
    sent_count = 0
    for recipient in recipients[:scheduled.max_recipients or len(recipients)]:
        if send_email_to_user(scheduled.event, recipient, scheduled.subject, scheduled.content):
            sent_count += 1
    
    scheduled.sent_count += sent_count
    scheduled.last_sent_at = timezone.now()
    scheduled.save()
    
    messages.success(request, f'Sent {sent_count} emails successfully!')
    return redirect('communication:scheduled_emails')


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def send_email(request):
    """Send a custom email to event attendees"""
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        recipient_filter = request.POST.get('recipient_filter', '{}')
        
        event = get_object_or_404(Event, id=event_id)
        
        try:
            import json
            filter_dict = json.loads(recipient_filter) if recipient_filter else {}
        except:
            filter_dict = {}
        
        recipients = get_recipients_for_filter(event, filter_dict)
        
        sent_count = 0
        for recipient in recipients:
            if send_email_to_user(event, recipient, subject, content):
                sent_count += 1
        
        messages.success(request, f'Sent {sent_count} emails successfully!')
        return redirect('communication:email_logs')
    
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'communication/send_email.html', {'events': events})


# ============ SMS Notifications ============

@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def sms_list(request):
    """List SMS notifications"""
    sms = SMSNotification.objects.all()[:100]
    return render(request, 'communication/sms_list.html', {'sms': sms})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def sms_send(request):
    """Send SMS notification"""
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        message = request.POST.get('message')
        
        event = get_object_or_404(Event, id=event_id)
        registrations = Registration.objects.filter(event=event, status='confirmed')
        
        sent_count = 0
        for reg in registrations:
            if reg.user and reg.user.phone:
                sms = SMSNotification.objects.create(
                    event=event,
                    recipient=reg.user,
                    phone_number=reg.user.phone,
                    message=message[:160]
                )
                # In production, integrate with Twilio or other SMS provider
                sms.mark_sent()
                sent_count += 1
        
        messages.success(request, f'Sent {sent_count} SMS notifications!')
        return redirect('communication:sms_list')
    
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'communication/sms_send.html', {'events': events})


# ============ Push Notifications ============

@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def push_list(request):
    """List push notifications"""
    pushes = PushNotification.objects.all()[:100]
    return render(request, 'communication/push_list.html', {'pushes': pushes})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def push_send(request):
    """Send push notification"""
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        title = request.POST.get('title')
        message = request.POST.get('message')
        platform = request.POST.get('platform', 'all')
        
        event = get_object_or_404(Event, id=event_id)
        
        push = PushNotification.objects.create(
            event=event,
            title=title,
            message=message,
            platform=platform
        )
        
        # In production, integrate with Firebase or other push service
        registrations = Registration.objects.filter(event=event, status='confirmed').count()
        push.sent_count = registrations
        push.is_sent = True
        push.sent_at = timezone.now()
        push.save()
        
        messages.success(request, 'Push notification sent successfully!')
        return redirect('communication:push_list')
    
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'communication/push_send.html', {'events': events})


# ============ Live Polls ============

@login_required
def poll_list(request):
    """List all polls for user's events"""
    polls = LivePoll.objects.filter(event__organizer=request.user)
    return render(request, 'communication/poll_list.html', {'polls': polls})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def poll_create(request):
    """Create a new live poll"""
    if request.method == 'POST':
        form = LivePollForm(request.POST)
        if form.is_valid():
            poll = form.save()
            messages.success(request, 'Poll created successfully!')
            return redirect('communication:poll_detail', poll_id=poll.id)
    else:
        form = LivePollForm()
        if 'event_id' in request.GET:
            form.fields['event'].initial = request.GET['event_id']
    
    return render(request, 'communication/poll_form.html', {'form': form})


@login_required
def poll_detail(request, poll_id):
    """View poll details and results"""
    poll = get_object_or_404(LivePoll, id=poll_id)
    responses = poll.responses.all()
    
    # Calculate results
    results = {}
    if poll.poll_type in ['single', 'multiple']:
        for option in poll.options:
            results[option] = responses.filter(selected_options__contains=[option]).count()
    elif poll.poll_type == 'rating':
        ratings = [r.rating_value for r in responses if r.rating_value]
        if ratings:
            results['average'] = sum(ratings) / len(ratings)
            results['count'] = len(ratings)
    
    context = {
        'poll': poll,
        'responses': responses,
        'results': results,
        'total_responses': responses.count(),
    }
    return render(request, 'communication/poll_detail.html', context)


@login_required
def poll_vote(request, poll_id):
    """Submit a vote for a poll"""
    poll = get_object_or_404(LivePoll, id=poll_id)
    
    if not poll.is_active:
        return JsonResponse({'success': False, 'message': 'Poll is closed'})
    
    if request.method == 'POST':
        from .forms import PollResponseForm
        form = PollResponseForm(request.POST)
        
        if form.is_valid():
            selected_options = form.cleaned_data.get('selected_options', [])
            rating_value = form.cleaned_data.get('rating_value')
            wordcloud_response = form.cleaned_data.get('wordcloud_response')
            
            response, created = PollResponse.objects.update_or_create(
                poll=poll,
                user=request.user,
                defaults={
                    'selected_options': selected_options,
                    'rating_value': rating_value,
                    'wordcloud_response': wordcloud_response,
                }
            )
            
            return JsonResponse({'success': True, 'message': 'Vote submitted successfully!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def poll_close(request, poll_id):
    """Close a poll"""
    poll = get_object_or_404(LivePoll, id=poll_id)
    poll.is_active = False
    poll.ends_at = timezone.now()
    poll.save()
    messages.success(request, 'Poll closed successfully!')
    return redirect('communication:poll_detail', poll_id=poll.id)


@login_required
def poll_results(request, poll_id):
    """Get poll results as JSON"""
    poll = get_object_or_404(LivePoll, id=poll_id)
    responses = poll.responses.all()
    
    results = {}
    if poll.poll_type in ['single', 'multiple']:
        for option in poll.options:
            results[option] = responses.filter(selected_options__contains=[option]).count()
    elif poll.poll_type == 'rating':
        ratings = [r.rating_value for r in responses if r.rating_value]
        if ratings:
            results['average'] = round(sum(ratings) / len(ratings), 2)
            results['count'] = len(ratings)
    
    return JsonResponse({
        'success': True,
        'poll': {
            'id': poll.id,
            'question': poll.question,
            'is_active': poll.is_active,
        },
        'results': results,
        'total_responses': responses.count(),
    })


# ============ Live Q&A ============

@login_required
def qa_list(request):
    """List all Q&A sessions"""
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'communication/qa_list.html', {'events': events})


@login_required
def qa_event(request, event_id):
    """View Q&A for a specific event"""
    event = get_object_or_404(Event, id=event_id)
    questions = LiveQA.objects.filter(event=event, is_approved=True).order_by('-upvotes', '-created_at')
    
    # Check if user can moderate
    can_moderate = request.user == event.organizer or request.user.is_staff
    
    context = {
        'event': event,
        'questions': questions,
        'can_moderate': can_moderate,
    }
    return render(request, 'communication/qa_event.html', context)


@login_required
def qa_ask(request, event_id):
    """Ask a question in Q&A"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = LiveQAForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.event = event
            question.user = request.user
            question.save()
            messages.success(request, 'Question submitted successfully!')
            return redirect('communication:qa_event', event_id=event.id)
    else:
        form = LiveQAForm()
    
    return render(request, 'communication/qa_ask.html', {'form': form, 'event': event})


@login_required
def qa_upvote(request, question_id):
    """Upvote a Q&A question"""
    question = get_object_or_404(LiveQA, id=question_id)
    
    if question.upvote(request.user.id):
        return JsonResponse({'success': True, 'upvotes': question.upvotes})
    return JsonResponse({'success': False, 'message': 'Already upvoted'})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def qa_answer(request, question_id):
    """Mark a question as answered"""
    question = get_object_or_404(LiveQA, id=question_id)
    
    if request.method == 'POST':
        answer = request.POST.get('answer', '')
        question.answer = answer
        question.is_answered = True
        question.answered_at = timezone.now()
        question.answered_by = request.user
        question.save()
        messages.success(request, 'Question marked as answered!')
        return redirect('communication:qa_event', event_id=question.event.id)
    
    return render(request, 'communication/qa_answer.html', {'question': question})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def qa_approve(request, question_id):
    """Approve/reject a Q&A question"""
    question = get_object_or_404(LiveQA, id=question_id)
    action = request.GET.get('action', 'approve')
    
    if action == 'approve':
        question.is_approved = True
        messages.success(request, 'Question approved!')
    else:
        question.is_approved = False
        messages.success(request, 'Question rejected!')
    
    question.save()
    return redirect('communication:qa_event', event_id=question.event.id)


# ============ Reminders ============

@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def reminder_list(request):
    """List reminder settings"""
    reminders = AutomatedReminder.objects.all()
    return render(request, 'communication/reminder_list.html', {'reminders': reminders})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def reminder_create(request):
    """Create a new reminder"""
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        reminder_type = request.POST.get('reminder_type')
        trigger = request.POST.get('trigger')
        message = request.POST.get('message_template')
        
        event = get_object_or_404(Event, id=event_id)
        
        AutomatedReminder.objects.create(
            event=event,
            reminder_type=reminder_type,
            trigger=trigger,
            message_template=message
        )
        
        messages.success(request, 'Reminder created successfully!')
        return redirect('communication:reminder_list')
    
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'communication/reminder_form.html', {'events': events})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def reminder_edit(request, reminder_id):
    """Edit a reminder"""
    reminder = get_object_or_404(AutomatedReminder, id=reminder_id)
    
    if request.method == 'POST':
        reminder.reminder_type = request.POST.get('reminder_type')
        reminder.trigger = request.POST.get('trigger')
        reminder.message_template = request.POST.get('message_template')
        reminder.is_active = 'is_active' in request.POST
        reminder.save()
        
        messages.success(request, 'Reminder updated successfully!')
        return redirect('communication:reminder_list')
    
    return render(request, 'communication/reminder_form.html', {'reminder': reminder})


@user_passes_test(lambda u: u.is_staff or u.is_organizer)
def reminder_delete(request, reminder_id):
    """Delete a reminder"""
    reminder = get_object_or_404(AutomatedReminder, id=reminder_id)
    reminder.delete()
    messages.success(request, 'Reminder deleted successfully!')
    return redirect('communication:reminder_list')


# ============ Helper Functions ============

def get_recipients_for_filter(event, filter_dict):
    """Get recipients based on filter criteria"""
    registrations = Registration.objects.filter(event=event, status='confirmed')
    
    if 'status' in filter_dict:
        registrations = registrations.filter(status=filter_dict['status'])
    
    recipients = []
    for reg in registrations:
        if reg.user:
            recipients.append(reg.user)
        elif reg.attendee_email:
            # Create a simple user-like object for non-registered attendees
            recipients.append(type('User', (), {'email': reg.attendee_email, 'first_name': reg.attendee_name.split()[0] if reg.attendee_name else ''})())
    
    return recipients


def send_email_to_user(event, user, subject, content):
    """Send an email to a user"""
    try:
        # Log the email
        log = EmailLog.objects.create(
            recipient=user.email,
            recipient_user=getattr(user, 'id', None),
            event=event,
            subject=subject,
            content=content,
            status='pending'
        )
        
        # In production, actually send the email
        # send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, [user.email])
        
        log.mark_sent()
        return True
    except Exception as e:
        log.mark_failed(str(e))
        return False


def send_event_reminders():
    """Send automated event reminders (called by cron/celery)"""
    now = timezone.now()
    
    # Find reminders that should be sent
    reminders = AutomatedReminder.objects.filter(is_active=True)
    
    for reminder in reminders:
        event = reminder.event
        
        # Calculate trigger time
        if reminder.trigger == '24_hours':
            target_time = event.start_date - timezone.timedelta(hours=24)
        elif reminder.trigger == '1_hour':
            target_time = event.start_date - timezone.timedelta(hours=1)
        elif reminder.trigger == '30_minutes':
            target_time = event.start_date - timezone.timedelta(minutes=30)
        elif reminder.trigger == '15_minutes':
            target_time = event.start_date - timezone.timedelta(minutes=15)
        else:
            continue
        
        # Check if it's time to send
        if now >= target_time and (not reminder.last_sent_at or (now - reminder.last_sent_at).days >= 1):
            registrations = Registration.objects.filter(event=event, status='confirmed')
            
            for reg in registrations:
                if reg.user:
                    send_email_to_user(event, reg.user, f"Reminder: {event.title}", reminder.message_template)
            
            reminder.last_sent_at = now
            reminder.save()