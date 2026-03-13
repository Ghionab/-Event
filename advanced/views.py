from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import FileResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

from .models import (
    Vendor, VendorContact, Contract, VendorPayment,
    TeamMember, Task, TaskComment, TeamNotification,
    AuditLog, DataExport, PrivacySetting, SecurityEvent
)
from .forms import (
    VendorForm, VendorContactForm, ContractForm, VendorPaymentForm,
    TeamMemberForm, TaskForm, TaskCommentForm, AuditLogFilterForm,
    PrivacySettingForm
)
from events.models import Event
from users.models import User


# ============ Vendor Views ============

@login_required
@permission_required('advanced.view_vendor', raise_exception=True)
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
@permission_required('advanced.add_vendor', raise_exception=True)
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
@permission_required('advanced.view_vendor', raise_exception=True)
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
@permission_required('advanced.change_vendor', raise_exception=True)
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
@permission_required('advanced.delete_vendor', raise_exception=True)
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        vendor.delete()
        messages.success(request, 'Vendor deleted successfully.')
        return redirect('advanced:vendor_list')
    
    return render(request, 'advanced/vendor_confirm_delete.html', {'vendor': vendor})


@login_required
@permission_required('advanced.view_vendorcontact', raise_exception=True)
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
@permission_required('advanced.view_contract', raise_exception=True)
def vendor_contracts(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    contracts = vendor.contracts.order_by('-created_at')
    return render(request, 'advanced/vendor_contracts.html', {'vendor': vendor, 'contracts': contracts})


# ============ Contract Views ============

@login_required
@permission_required('advanced.view_contract', raise_exception=True)
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
@permission_required('advanced.add_contract', raise_exception=True)
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
@permission_required('advanced.view_contract', raise_exception=True)
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    payments = contract.payments.order_by('due_date')
    
    return render(request, 'advanced/contract_detail.html', {
        'contract': contract,
        'payments': payments
    })


@login_required
@permission_required('advanced.change_contract', raise_exception=True)
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
@permission_required('advanced.delete_contract', raise_exception=True)
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    
    if request.method == 'POST':
        contract.delete()
        messages.success(request, 'Contract deleted successfully.')
        return redirect('advanced:contract_list')
    
    return render(request, 'advanced/contract_confirm_delete.html', {'contract': contract})


@login_required
@permission_required('advanced.view_vendorpayment', raise_exception=True)
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
@permission_required('advanced.view_teammember', raise_exception=True)
def team_list(request):
    team_members = TeamMember.objects.filter(is_active=True)
    
    event_id = request.GET.get('event')
    if event_id:
        team_members = team_members.filter(event_id=event_id)
    
    role = request.GET.get('role')
    if role:
        team_members = team_members.filter(role=role)
    
    events = Event.objects.all()
    return render(request, 'advanced/team_list.html', {
        'team_members': team_members,
        'events': events
    })


@login_required
@permission_required('advanced.add_teammember', raise_exception=True)
def team_member_create(request):
    # Get event from query parameter
    event_id = request.GET.get('event')
    event = None
    if event_id:
        event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, user=request.user)
        if form.is_valid():
            team_member = form.save(commit=False)
            # Set event if not already set
            if not team_member.event and event:
                team_member.event = event
            # If still no event, try to get from POST data
            if not team_member.event:
                event_id_post = request.POST.get('event')
                if event_id_post:
                    team_member.event = get_object_or_404(Event, pk=event_id_post)
            team_member.save()
            messages.success(request, 'Team member added successfully.')
            
            # Redirect back to event setup if event parameter is present
            if event:
                return redirect('organizer_event_setup', event_id=event.id)
            return redirect('advanced:team_list')
    else:
        initial = {}
        if event:
            initial['event'] = event
        form = TeamMemberForm(initial=initial, user=request.user)
    
    # Get events for dropdown
    if request.user.is_staff:
        events = Event.objects.all()
    else:
        events = Event.objects.filter(organizer=request.user)
    
    return render(request, 'advanced/team_member_form.html', {
        'form': form, 
        'action': 'Add',
        'event': event,
        'events': events
    })


@login_required
@permission_required('advanced.change_teammember', raise_exception=True)
def team_member_update(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    
    # Check if coming from event setup (GET or POST)
    from_event_setup = request.GET.get('from_setup') or request.POST.get('from_setup')
    event_id = request.GET.get('event') or request.POST.get('event') or (member.event.id if member.event else None)
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, instance=member, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team member updated successfully.')
            
            # Redirect back to event setup if from_setup parameter is present
            if from_event_setup and event_id:
                return redirect('organizer_event_setup', event_id=event_id)
            return redirect('advanced:team_list')
    else:
        form = TeamMemberForm(instance=member, user=request.user)
    
    return render(request, 'advanced/team_member_form.html', {
        'form': form, 
        'action': 'Update', 
        'member': member,
        'from_event_setup': from_event_setup,
        'event_id': event_id
    })


@login_required
@permission_required('advanced.delete_teammember', raise_exception=True)
def team_member_delete(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    
    # Check if coming from event setup (GET or POST)
    from_event_setup = request.GET.get('from_setup') or request.POST.get('from_setup')
    event_id = request.GET.get('event') or request.POST.get('event') or (member.event.id if member.event else None)
    
    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Team member removed successfully.')
        
        # Redirect back to event setup if from_setup parameter is present
        if from_event_setup and event_id:
            return redirect('organizer_event_setup', event_id=event_id)
        return redirect('advanced:team_list')
    
    return render(request, 'advanced/team_member_confirm_delete.html', {
        'member': member,
        'from_event_setup': from_event_setup,
        'event_id': event_id
    })


# ============ Task Views ============

@login_required
@permission_required('advanced.view_task', raise_exception=True)
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
@permission_required('advanced.add_task', raise_exception=True)
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
@permission_required('advanced.view_task', raise_exception=True)
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
@permission_required('advanced.change_task', raise_exception=True)
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
@permission_required('advanced.delete_task', raise_exception=True)
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
@permission_required('advanced.view_task', raise_exception=True)
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
@permission_required('advanced.change_task', raise_exception=True)
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
@permission_required('advanced.view_auditlog', raise_exception=True)
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
@permission_required('advanced.view_securityevent', raise_exception=True)
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
@permission_required('advanced.change_securityevent', raise_exception=True)
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