from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

from .models import (
    Vendor, VendorContact, Contract, VendorPayment,
    TeamMember, Task, TaskComment, TeamNotification,
    AuditLog, DataExport, PrivacySetting, SecurityEvent,
    UsherAssignment
)
from .forms import (
    VendorForm, VendorContactForm, ContractForm, VendorPaymentForm,
    TeamMemberForm, TeamMemberCreateForm, TeamMemberUpdateForm, TaskForm, TaskCommentForm, AuditLogFilterForm,
    PrivacySettingForm
)
from events.models import Event
from users.models import User
import secrets
import string


# ============ Vendor Views ============

@login_required
def vendor_list(request):
    vendors = Vendor.objects.filter(is_blacklisted=False)
    
    category = request.GET.get('category')
    if category:
        vendors = vendors.filter(category=category)
    
    search = request.GET.get('search')
    if search:
        vendors = vendors.filter(
            Q(name__icontains=search) |
            Q(contact_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    vendors = vendors.order_by('-is_preferred', 'name')
    
    return render(request, 'advanced/vendor_list.html', {'vendors': vendors})


@login_required
def vendor_create(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save()
            messages.success(request, f'Vendor {vendor.name} created successfully.')
            return redirect('advanced:vendor_detail', pk=vendor.pk)
    else:
        form = VendorForm()
    
    return render(request, 'advanced/vendor_form.html', {'form': form, 'action': 'Create'})


@login_required
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    contacts = vendor.contacts.order_by('-contact_date')[:10]
    contracts = vendor.contracts.order_by('-created_at')[:5]
    
    return render(request, 'advanced/vendor_detail.html', {
        'vendor': vendor,
        'contacts': contacts,
        'contracts': contracts
    })


@login_required
def vendor_update(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor updated successfully.')
            return redirect('advanced:vendor_detail', pk=vendor.pk)
    else:
        form = VendorForm(instance=vendor)
    
    return render(request, 'advanced/vendor_form.html', {'form': form, 'action': 'Update', 'vendor': vendor})


@login_required
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        vendor.delete()
        messages.success(request, 'Vendor deleted successfully.')
        return redirect('advanced:vendor_list')
    
    return render(request, 'advanced/vendor_confirm_delete.html', {'vendor': vendor})


@login_required
def vendor_contacts(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        form = VendorContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.vendor = vendor
            contact.created_by = request.user
            contact.save()
            messages.success(request, 'Contact added successfully.')
            return redirect('advanced:vendor_contacts', pk=vendor.pk)
    else:
        form = VendorContactForm(initial={'vendor': vendor})
    
    contacts = vendor.contacts.order_by('-contact_date')
    return render(request, 'advanced/vendor_contacts.html', {
        'vendor': vendor,
        'contacts': contacts,
        'form': form
    })


@login_required
def vendor_contracts(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    contracts = vendor.contracts.order_by('-created_at')
    return render(request, 'advanced/vendor_contracts.html', {'vendor': vendor, 'contracts': contracts})


# ============ Contract Views ============

@login_required
def contract_list(request):
    contracts = Contract.objects.all()
    
    status = request.GET.get('status')
    if status:
        contracts = contracts.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        contracts = contracts.filter(
            Q(title__icontains=search) |
            Q(vendor__name__icontains=search)
        )
    
    contracts = contracts.order_by('-created_at')
    return render(request, 'advanced/contract_list.html', {'contracts': contracts})


@login_required
def contract_create(request):
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save()
            messages.success(request, 'Contract created successfully.')
            return redirect('advanced:contract_detail', pk=contract.pk)
    else:
        form = ContractForm()
    
    return render(request, 'advanced/contract_form.html', {'form': form, 'action': 'Create'})


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    payments = contract.payments.order_by('due_date')
    
    return render(request, 'advanced/contract_detail.html', {
        'contract': contract,
        'payments': payments
    })


@login_required
def contract_update(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contract updated successfully.')
            return redirect('advanced:contract_detail', pk=contract.pk)
    else:
        form = ContractForm(instance=contract)
    
    return render(request, 'advanced/contract_form.html', {'form': form, 'action': 'Update', 'contract': contract})


@login_required
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        contract.delete()
        messages.success(request, 'Contract deleted successfully.')
        return redirect('advanced:contract_list')
    
    return render(request, 'advanced/contract_confirm_delete.html', {'contract': contract})


@login_required
def contract_payments(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        form = VendorPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.contract = contract
            payment.vendor = contract.vendor
            payment.save()
            messages.success(request, 'Payment added successfully.')
            return redirect('advanced:contract_payments', pk=contract.pk)
    else:
        form = VendorPaymentForm(initial={'contract': contract, 'vendor': contract.vendor})
    
    payments = contract.payments.order_by('due_date')
    return render(request, 'advanced/contract_payments.html', {
        'contract': contract,
        'payments': payments,
        'form': form
    })


# ============ Team Views ============

@login_required
def team_list(request):
    """Display all team members"""
    team_members = TeamMember.objects.filter(is_active=True).select_related('user')
    
    return render(request, 'advanced/team_list.html', {
        'team_members': team_members
    })


@login_required
def team_member_create(request):
    """Create a new team member with user account"""
    # Get event from query parameter
    event_id = request.GET.get('event')
    event = None
    if event_id:
        event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = TeamMemberCreateForm(request.POST)
        if form.is_valid():
            try:
                team_member = form.save(request, event)
                messages.success(request, f'Team member {team_member.user.email} created successfully!')
                
                # Redirect back to event setup if event parameter is present
                if event:
                    return redirect('organizers:organizer_event_setup', event_id=event.id)
                return redirect('advanced:team_list')
            except Exception as e:
                messages.error(request, f'Error creating team member: {str(e)}')
    else:
        form = TeamMemberCreateForm()
    
    return render(request, 'advanced/team_member_create.html', {
        'form': form,
        'event': event
    })


@login_required
def team_member_update(request, pk):
    """Update an existing team member"""
    team_member = get_object_or_404(TeamMember, pk=pk, is_active=True)
    
    if request.method == 'POST':
        form = TeamMemberUpdateForm(request.POST, team_member=team_member)
        if form.is_valid():
            try:
                updated_member = form.save()
                messages.success(request, f'Team member {updated_member.user.email} updated successfully!')
                return redirect('advanced:team_list')
            except Exception as e:
                messages.error(request, f'Error updating team member: {str(e)}')
    else:
        form = TeamMemberUpdateForm(team_member=team_member)
    
    return render(request, 'advanced/team_member_update.html', {
        'form': form,
        'team_member': team_member
    })


@login_required
def team_member_delete(request, pk):
    """Delete a team member"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    if request.method == 'POST':
        user_email = team_member.user.email
        # Soft delete by setting is_active to False
        team_member.is_active = False
        team_member.save()
        
        # Optionally deactivate the user account as well
        team_member.user.is_active = False
        team_member.user.save()
        
        messages.success(request, f'Team member {user_email} removed successfully!')
        return redirect('advanced:team_list')
    
    return render(request, 'advanced/team_member_confirm_delete.html', {
        'member': team_member
    })


# ============ Task Views ============

@login_required
def task_list(request):
    # Get user's events (organizer only sees their events)
    if request.user.is_staff:
        tasks = Task.objects.all()
        events = Event.objects.all()
    else:
        events = Event.objects.filter(organizer=request.user)
        tasks = Task.objects.filter(event__in=events)
    
    # Filtering
    event_id = request.GET.get('event')
    if event_id:
        tasks = tasks.filter(event_id=event_id)
    
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    priority = request.GET.get('priority')
    if priority:
        tasks = tasks.filter(priority=priority)
    
    assigned_to = request.GET.get('assigned_to')
    if assigned_to:
        tasks = tasks.filter(assigned_to_id=assigned_to)
    
    # Search
    search = request.GET.get('search')
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__icontains=search)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    tasks = tasks.order_by(sort_by)
    
    # Pass status and priority choices to template
    statuses = Task.STATUS_CHOICES
    priorities = Task.PRIORITY_CHOICES
    
    # Get team members for filter
    team_members = TeamMember.objects.filter(event__in=events, is_active=True).distinct()
    
    # Task statistics
    stats = {
        'total': tasks.count(),
        'todo': tasks.filter(status='todo').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'completed': tasks.filter(status='completed').count(),
        'overdue': sum(1 for task in tasks if task.is_overdue()),
    }
    
    return render(request, 'advanced/task_list.html', {
        'tasks': tasks,
        'events': events,
        'statuses': statuses,
        'priorities': priorities,
        'team_members': team_members,
        'stats': stats,
    })


@login_required
def task_create(request):
    # Get event from query parameter
    event_id = request.GET.get('event')
    event = None
    if event_id:
        event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, event=event, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            # Set event if not already set
            if not task.event and event:
                task.event = event
            task.save()
            messages.success(request, 'Task created successfully.')
            return redirect('advanced:task_detail', pk=task.pk)
    else:
        initial = {}
        if event:
            initial['event'] = event
        form = TaskForm(initial=initial, event=event, user=request.user)
    
    return render(request, 'advanced/task_form.html', {'form': form, 'action': 'Create', 'event': event})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    comments = task.comments.order_by('created_at')
    
    if request.method == 'POST':
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added.')
            return redirect('advanced:task_detail', pk=task.pk)
    else:
        form = TaskCommentForm()
    
    return render(request, 'advanced/task_detail.html', {
        'task': task,
        'comments': comments,
        'form': form
    })


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task, event=task.event, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('advanced:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, event=task.event, user=request.user)
    
    return render(request, 'advanced/task_form.html', {'form': form, 'action': 'Update', 'task': task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('advanced:task_list')
    
    return render(request, 'advanced/task_confirm_delete.html', {'task': task})


@login_required
def task_add_comment(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added.')
    
    return redirect('advanced:task_detail', pk=task.pk)


@login_required
def task_export(request):
    """Export tasks to CSV"""
    import csv
    from django.http import HttpResponse
    
    # Get user's events (organizer only sees their events)
    if request.user.is_staff:
        tasks = Task.objects.all()
    else:
        events = Event.objects.filter(organizer=request.user)
        tasks = Task.objects.filter(event__in=events)
    
    # Apply filters from query parameters
    event_id = request.GET.get('event')
    if event_id:
        tasks = tasks.filter(event_id=event_id)
    
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    priority = request.GET.get('priority')
    if priority:
        tasks = tasks.filter(priority=priority)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Event', 'Title', 'Description', 'Status', 'Priority',
        'Assigned To', 'Due Date', 'Progress %', 'Estimated Hours',
        'Actual Hours', 'Tags', 'Created At', 'Completed At'
    ])
    
    for task in tasks.select_related('event', 'assigned_to', 'assigned_to__user'):
        writer.writerow([
            task.event.title,
            task.title,
            task.description,
            task.get_status_display(),
            task.get_priority_display(),
            task.assigned_to.user.email if task.assigned_to else '',
            task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else '',
            task.progress_percentage,
            task.estimated_hours or '',
            task.actual_hours or '',
            task.tags,
            task.created_at.strftime('%Y-%m-%d %H:%M'),
            task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else ''
        ])
    
    return response


@login_required
def task_bulk_update(request):
    """Bulk update task status or priority"""
    if request.method == 'POST':
        task_ids = request.POST.getlist('task_ids')
        action = request.POST.get('action')
        
        if not task_ids:
            messages.error(request, 'No tasks selected.')
            return redirect('advanced:task_list')
        
        # Get user's events (organizer only sees their events)
        if request.user.is_staff:
            tasks = Task.objects.filter(id__in=task_ids)
        else:
            events = Event.objects.filter(organizer=request.user)
            tasks = Task.objects.filter(id__in=task_ids, event__in=events)
        
        if action == 'mark_completed':
            for task in tasks:
                task.mark_completed()
            messages.success(request, f'{tasks.count()} tasks marked as completed.')
        
        elif action == 'change_status':
            new_status = request.POST.get('new_status')
            if new_status:
                tasks.update(status=new_status)
                messages.success(request, f'{tasks.count()} tasks updated to {new_status}.')
        
        elif action == 'change_priority':
            new_priority = request.POST.get('new_priority')
            if new_priority:
                tasks.update(priority=new_priority)
                messages.success(request, f'{tasks.count()} tasks updated to {new_priority} priority.')
        
        elif action == 'delete':
            count = tasks.count()
            tasks.delete()
            messages.success(request, f'{count} tasks deleted.')
        
        return redirect('advanced:task_list')
    
    return redirect('advanced:task_list')


# ============ Audit Views ============

@login_required
def audit_log(request):
    logs = AuditLog.objects.all()
    
    form = AuditLogFilterForm(request.GET)
    
    if form.is_valid():
        action = form.cleaned_data.get('action')
        user_id = form.cleaned_data.get('user')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if action:
            logs = logs.filter(action=action)
        if user_id:
            logs = logs.filter(user_id=user_id)
        if start_date:
            logs = logs.filter(created_at__date__gte=start_date)
        if end_date:
            logs = logs.filter(created_at__date__lte=end_date)
    
    logs = logs[:100]
    
    users = User.objects.all()
    return render(request, 'advanced/audit_log.html', {
        'logs': logs,
        'form': form,
        'users': users
    })


# ============ Security Views ============

@login_required
def security_events(request):
    events = SecurityEvent.objects.all()
    
    event_type = request.GET.get('type')
    if event_type:
        events = events.filter(event_type=event_type)
    
    severity = request.GET.get('severity')
    if severity:
        events = events.filter(severity=severity)
    
    resolved = request.GET.get('resolved')
    if resolved == 'yes':
        events = events.filter(is_resolved=True)
    elif resolved == 'no':
        events = events.filter(is_resolved=False)
    
    events = events.order_by('-created_at')
    return render(request, 'advanced/security_events.html', {'events': events})


@login_required
def security_event_resolve(request, pk):
    event = get_object_or_404(SecurityEvent, pk=pk)
    
    if request.method == 'POST':
        notes = request.POST.get('resolution_notes', '')
        event.is_resolved = True
        event.resolved_at = timezone.now()
        event.resolved_by = request.user
        event.resolution_notes = notes
        event.save()
        messages.success(request, 'Security event resolved.')
        return redirect('advanced:security_events')
    
    return render(request, 'advanced/security_event_resolve.html', {'event': event})


# ============ Privacy Views ============

@login_required
def privacy_settings(request):
    setting, created = PrivacySetting.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PrivacySettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Privacy settings updated.')
            return redirect('advanced:privacy_settings')
    else:
        form = PrivacySettingForm(instance=setting)
    
    return render(request, 'advanced/privacy_settings.html', {'form': form})


@login_required
def data_export_request(request):
    if request.method == 'POST':
        export_type = request.POST.get('export_type', 'all')
        formats = request.POST.getlist('formats', ['json'])
        
        export = DataExport.objects.create(
            user=request.user,
            export_type=export_type,
            formats=formats,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        messages.success(request, 'Data export requested. You will be notified when ready.')
        return redirect('advanced:privacy_settings')
    
    return render(request, 'advanced/data_export_request.html')


@login_required
def data_export_download(request, pk):
    export = get_object_or_404(DataExport, pk=pk, user=request.user)
    
    if export.status != 'completed':
        messages.error(request, 'Export is not ready yet.')
        return redirect('advanced:privacy_settings')
    
    if export.expires_at < timezone.now():
        messages.error(request, 'This export has expired.')
        return redirect('advanced:privacy_settings')
    
    if export.file:
        response = FileResponse(export.file)
        response['Content-Disposition'] = f'attachment; filename="data_export_{export.pk}.zip"'
        return response
    
    return HttpResponseForbidden('File not found.')


# ============ Usher Assignment Views ============

def generate_temp_password(length=12):
    """Generate a random temporary password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@login_required
def usher_list(request):
    """List all usher assignments for events organized by current user"""
    can_manage_ushers = (
        request.user.is_superuser
        or request.user.is_staff
        or request.user.role in ['admin', 'staff']
        or getattr(request.user, 'is_organizer', False)
    )

    if not can_manage_ushers:
        messages.error(request, 'You do not have permission to view usher assignments.')
        return redirect('organizers:organizer_dashboard')
    
    if getattr(request.user, 'is_organizer', False) and request.user.role not in ['admin', 'staff'] and not request.user.is_staff and not request.user.is_superuser:
        assignments = UsherAssignment.objects.filter(
            event__organizer=request.user
        ).select_related('event', 'user')
        events = Event.objects.filter(organizer=request.user)
    else:
        assignments = UsherAssignment.objects.select_related('event', 'user')
        events = Event.objects.all()
    
    event_id = request.GET.get('event')
    if event_id:
        assignments = assignments.filter(event_id=event_id)

    return render(request, 'advanced/usher_list.html', {
        'assignments': assignments,
        'events': events
    })


@login_required
def usher_create(request):
    """Create new usher assignment with manually entered credentials"""
    can_manage_ushers = (
        request.user.is_superuser
        or request.user.is_staff
        or request.user.role in ['admin', 'staff']
        or getattr(request.user, 'is_organizer', False)
    )

    if not can_manage_ushers:
        messages.error(request, 'You do not have permission to create usher assignments.')
        return redirect('organizers:organizer_dashboard')

    event_id = request.GET.get('event')
    event = None
    if event_id:
        if request.user.role in ['admin', 'staff'] or request.user.is_staff or request.user.is_superuser:
            event = get_object_or_404(Event, pk=event_id)
        else:
            event = get_object_or_404(Event, pk=event_id, organizer=request.user)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        event_id_post = request.POST.get('event')
        venue_name = request.POST.get('venue_name')
        
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect('advanced:usher_create')
        
        if not event_id_post:
            messages.error(request, 'Please select an event.')
            return redirect('advanced:usher_create')
        
        if not venue_name:
            messages.error(request, 'Please select a venue.')
            return redirect('advanced:usher_create')
        
        if request.user.role in ['admin', 'staff'] or request.user.is_staff or request.user.is_superuser:
            event = get_object_or_404(Event, pk=event_id_post)
        else:
            event = get_object_or_404(Event, pk=event_id_post, organizer=request.user)
        
        # Validate that venue belongs to the selected event
        from events.models import EventSession
        valid_venues = [event.venue_name] if event.venue_name else []
        session_venues = EventSession.objects.filter(
            event=event,
            location__isnull=False
        ).exclude(location='').values_list('location', flat=True).distinct()
        valid_venues.extend(list(session_venues))
        
        if venue_name not in valid_venues:
            messages.error(request, f'Invalid venue selection. Please select a venue associated with {event.title}.')
            # Get events for form re-render
            if request.user.role in ['admin', 'staff'] or request.user.is_staff or request.user.is_superuser:
                events = Event.objects.all()
            else:
                events = Event.objects.filter(organizer=request.user)
            
            return render(request, 'advanced/usher_form.html', {
                'event': event,
                'events': events,
                'action': 'Create',
                'selected_event_id': int(event_id_post) if event_id_post else None,
                'selected_venue': venue_name
            })
        
        # Check if user exists or create new
        user = User.objects.filter(email=email).first()
        if not user:
            # Create new user with usher role
            user = User.objects.create_user(
                email=email,
                password=password,
                role='usher',
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', '')
            )
        else:
            # Update existing user
            user.set_password(password)
            user.role = 'usher'
            user.is_active = True
            user.save()
        
        # Check if assignment already exists
        existing_assignment = UsherAssignment.objects.filter(
            user=user,
            event=event,
            venue_name=venue_name
        ).first()
        
        if existing_assignment:
            # Update existing assignment
            existing_assignment.is_active = True
            existing_assignment.temp_password = ''  # No temp password stored since manually set
            existing_assignment.save()
            messages.info(request, f'Usher assignment updated for {venue_name}.')
        else:
            # Create new usher assignment with venue name
            assignment = UsherAssignment.objects.create(
                user=user,
                event=event,
                venue_name=venue_name,
                temp_password=''  # No temp password stored since manually set
            )
            messages.success(request, f'Usher assigned successfully to {venue_name}.')
        
        return redirect('advanced:usher_list')
    
    # Get events for form
    if request.user.role in ['admin', 'staff'] or request.user.is_staff or request.user.is_superuser:
        events = Event.objects.all()
    else:
        events = Event.objects.filter(organizer=request.user)
    
    return render(request, 'advanced/usher_form.html', {
        'event': event,
        'events': events,
        'action': 'Create',
        'selected_event_id': event.pk if event else None,
        'selected_venue': event.venue_name if event else None
    })


@login_required
def usher_update(request, pk):
    """Update usher assignment (event, venue, status) with validation"""
    can_manage_ushers = (
        request.user.is_superuser
        or request.user.is_staff
        or request.user.role in ['admin', 'staff']
        or getattr(request.user, 'is_organizer', False)
    )

    if not can_manage_ushers:
        messages.error(request, 'You do not have permission to update usher assignments.')
        return redirect('organizers:organizer_dashboard')

    if request.user.role in ['admin', 'staff'] or request.user.is_staff or request.user.is_superuser:
        assignment = get_object_or_404(UsherAssignment, pk=pk)
        events = Event.objects.all()
    else:
        assignment = get_object_or_404(UsherAssignment, pk=pk, event__organizer=request.user)
        events = Event.objects.filter(organizer=request.user)
    
    if request.method == 'POST':
        # Get form data
        event_id = request.POST.get('event')
        venue_name = request.POST.get('venue_name', assignment.venue_name)
        
        # Validate event selection
        if event_id:
            if request.user.role in ['admin', 'staff'] or request.user.is_staff or request.user.is_superuser:
                new_event = get_object_or_404(Event, pk=event_id)
            else:
                new_event = get_object_or_404(Event, pk=event_id, organizer=request.user)
            
            # Validate that venue belongs to the selected event
            from events.models import EventSession
            valid_venues = [new_event.venue_name] if new_event.venue_name else []
            session_venues = EventSession.objects.filter(
                event=new_event,
                location__isnull=False
            ).exclude(location='').values_list('location', flat=True).distinct()
            valid_venues.extend(list(session_venues))
            
            if venue_name and valid_venues and venue_name not in valid_venues:
                messages.error(request, f'Invalid venue selection. Please select a venue associated with {new_event.title}.')
                return render(request, 'advanced/usher_form.html', {
                    'assignment': assignment,
                    'event': assignment.event,
                    'events': events,
                    'action': 'Update',
                    'selected_event_id': int(event_id) if event_id else None,
                    'selected_venue': venue_name
                })
            
            # Update event assignment
            assignment.event = new_event
        
        # Update venue and status
        assignment.venue_name = venue_name
        assignment.is_active = request.POST.get('is_active') == 'on'
        assignment.save()
        
        messages.success(request, 'Usher assignment updated successfully.')
        return redirect('advanced:usher_list')
    
    return render(request, 'advanced/usher_form.html', {
        'assignment': assignment,
        'event': assignment.event,
        'events': events,
        'action': 'Update',
        'selected_event_id': assignment.event.pk if assignment.event else None,
        'selected_venue': assignment.venue_name
    })


@login_required
def usher_delete(request, pk):
    """Delete usher assignment"""
    can_manage_ushers = (
        request.user.is_superuser
        or request.user.is_staff
        or request.user.role in ['admin', 'staff']
        or getattr(request.user, 'is_organizer', False)
    )

    if not can_manage_ushers:
        messages.error(request, 'You do not have permission to delete usher assignments.')
        return redirect('organizers:organizer_dashboard')

    if request.user.role in ['admin', 'staff'] or request.user.is_staff or request.user.is_superuser:
        assignment = get_object_or_404(UsherAssignment, pk=pk)
    else:
        assignment = get_object_or_404(UsherAssignment, pk=pk, event__organizer=request.user)
    
    if request.method == 'POST':
        user = assignment.user
        assignment.delete()
        
        # Optionally deactivate the user if they have no other assignments
        if not UsherAssignment.objects.filter(user=user).exists():
            user.is_active = False
            user.save()
        
        messages.success(request, 'Usher assignment removed.')
        return redirect('advanced:usher_list')
    
    return render(request, 'advanced/usher_confirm_delete.html', {'assignment': assignment})


@login_required
def ajax_get_event_venues(request, event_id):
    """AJAX endpoint to get venue options for an event"""
    can_manage_ushers = (
        request.user.is_superuser
        or request.user.is_staff
        or request.user.role in ['admin', 'staff']
        or getattr(request.user, 'is_organizer', False)
    )
    
    if not can_manage_ushers:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.user.role in ['admin', 'staff'] or request.user.is_staff or request.user.is_superuser:
        event = get_object_or_404(Event, pk=event_id)
    else:
        event = get_object_or_404(Event, pk=event_id, organizer=request.user)
    
    # Build list of venue options
    venues = []
    
    # Add main event venue if exists
    if event.venue_name:
        venues.append({
            'value': event.venue_name,
            'label': f"{event.venue_name} (Main Venue)"
        })
    
    # Add session locations as additional venue options
    from events.models import EventSession
    session_locations = EventSession.objects.filter(
        event=event,
        location__isnull=False
    ).exclude(
        location=''
    ).values_list('location', flat=True).distinct()
    
    for location in session_locations:
        if location != event.venue_name:  # Avoid duplicates
            venues.append({
                'value': location,
                'label': location
            })
    
    return JsonResponse({
        'event_id': event_id,
        'event_title': event.title,
        'venues': venues
    })