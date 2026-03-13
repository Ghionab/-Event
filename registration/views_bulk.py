"""
Enterprise Bulk Registration Views
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from events.models import Event
from .models import BulkRegistrationUpload, BulkRegistrationRow, BulkImportAuditLog
from .forms_bulk import (
    BulkUploadWizardForm, ColumnMappingForm, ImportOptionsForm, ValidationFilterForm
)
from .services.bulk_registration import BulkRegistrationService


@login_required
def bulk_registration_wizard_start(request, event_id):
    """Step 1: Start bulk registration wizard - File Upload"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to manage this event.')
        return redirect('organizer_event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = BulkUploadWizardForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create bulk upload record
                    bulk_upload = BulkRegistrationUpload.objects.create(
                        event=event,
                        uploaded_by=request.user,
                        file=form.cleaned_data['file'],
                        original_filename=form.cleaned_data['file'].name,
                        file_name=form.cleaned_data['file'].name,
                        file_size=form.cleaned_data['file'].size,
                        current_step='uploaded',
                        import_options={
                            'skip_header': form.cleaned_data['skip_header']
                        }
                    )
                    
                    # Parse file and detect columns
                    service = BulkRegistrationService(bulk_upload)
                    detected_columns, rows_data = service.parse_file()
                    
                    # Store detected columns
                    bulk_upload.detected_columns = detected_columns
                    bulk_upload.total_rows = len(rows_data)
                    bulk_upload.save()
                    
                    # Create row records
                    bulk_rows = []
                    for i, row_data in enumerate(rows_data, 1):
                        bulk_rows.append(BulkRegistrationRow(
                            bulk_upload=bulk_upload,
                            row_number=i,
                            row_data=row_data
                        ))
                    
                    BulkRegistrationRow.objects.bulk_create(bulk_rows)
                    
                    # Log audit
                    service._log_audit('upload', {
                        'filename': bulk_upload.original_filename,
                        'file_size': bulk_upload.file_size,
                        'total_rows': bulk_upload.total_rows,
                        'detected_columns': detected_columns
                    }, f'File uploaded with {len(rows_data)} rows and {len(detected_columns)} columns')
                    
                    messages.success(request, f'File uploaded successfully! Found {len(rows_data)} rows and {len(detected_columns)} columns.')
                    return redirect('registration:bulk_wizard_mapping', event_id=event.id, upload_id=bulk_upload.id)
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = BulkUploadWizardForm()
    
    # Get recent uploads for history
    recent_uploads = BulkRegistrationUpload.objects.filter(
        event=event
    ).order_by('-created_at')[:5]
    
    return render(request, 'registration/bulk_wizard_upload.html', {
        'event': event,
        'form': form,
        'recent_uploads': recent_uploads,
        'step': 1,
        'step_title': 'Upload File'
    })


@login_required
def bulk_registration_wizard_mapping(request, event_id, upload_id):
    """Step 2: Column Mapping"""
    event = get_object_or_404(Event, id=event_id)
    bulk_upload = get_object_or_404(BulkRegistrationUpload, id=upload_id, event=event)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to manage this event.')
        return redirect('organizer_event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = ColumnMappingForm(
            request.POST, 
            detected_columns=bulk_upload.detected_columns,
            event=event
        )
        if form.is_valid():
            # Build column mapping
            column_mapping = {}
            for field_name, system_field in form.cleaned_data.items():
                if field_name.startswith('mapping_'):
                    column_index = int(field_name.split('_')[1])
                    file_column = bulk_upload.detected_columns[column_index]
                    column_mapping[file_column] = system_field
            
            # Save mapping
            bulk_upload.column_mapping = column_mapping
            bulk_upload.current_step = 'mapped'
            bulk_upload.save()
            
            # Log audit
            service = BulkRegistrationService(bulk_upload)
            service._log_audit('mapping', {
                'column_mapping': column_mapping
            }, f'Column mapping configured for {len(column_mapping)} columns')
            
            messages.success(request, 'Column mapping saved successfully!')
            return redirect('registration:bulk_wizard_validation', event_id=event.id, upload_id=bulk_upload.id)
    else:
        form = ColumnMappingForm(
            detected_columns=bulk_upload.detected_columns,
            event=event
        )
    
    # Get sample data for preview
    sample_rows = bulk_upload.rows.order_by('row_number')[:5]
    
    return render(request, 'registration/bulk_wizard_mapping.html', {
        'event': event,
        'bulk_upload': bulk_upload,
        'form': form,
        'sample_rows': sample_rows,
        'step': 2,
        'step_title': 'Map Columns'
    })


@login_required
def bulk_registration_wizard_validation(request, event_id, upload_id):
    """Step 3: Data Validation and Preview"""
    event = get_object_or_404(Event, id=event_id)
    bulk_upload = get_object_or_404(BulkRegistrationUpload, id=upload_id, event=event)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to manage this event.')
        return redirect('organizer_event_detail', event_id=event.id)
    
    # Run validation if not done yet
    if bulk_upload.current_step == 'mapped':
        try:
            service = BulkRegistrationService(bulk_upload)
            validation_summary = service.validate_data()
            messages.success(request, f'Validation completed: {validation_summary["valid"]} valid, {validation_summary["warning"]} warnings, {validation_summary["error"]} errors')
        except Exception as e:
            messages.error(request, f'Validation failed: {str(e)}')
            return redirect('registration:bulk_wizard_mapping', event_id=event.id, upload_id=bulk_upload.id)
    
    # Handle form submission (proceed to options)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'proceed':
            return redirect('registration:bulk_wizard_options', event_id=event.id, upload_id=bulk_upload.id)
        elif action == 'back_to_mapping':
            return redirect('registration:bulk_wizard_mapping', event_id=event.id, upload_id=bulk_upload.id)
    
    # Get validation results with pagination
    filter_form = ValidationFilterForm(request.GET)
    
    rows_queryset = bulk_upload.rows.order_by('row_number')
    
    # Apply filters
    if filter_form.is_valid():
        status_filter = filter_form.cleaned_data.get('status_filter')
        search = filter_form.cleaned_data.get('search')
        
        if status_filter and status_filter != 'all':
            rows_queryset = rows_queryset.filter(validation_status=status_filter)
        
        if search:
            # Search in mapped data
            rows_queryset = rows_queryset.filter(
                mapped_data__icontains=search
            )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(rows_queryset, 50)  # Show 50 rows per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'registration/bulk_wizard_validation.html', {
        'event': event,
        'bulk_upload': bulk_upload,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'validation_summary': bulk_upload.validation_summary,
        'step': 3,
        'step_title': 'Validate Data'
    })


@login_required
def bulk_registration_wizard_options(request, event_id, upload_id):
    """Step 4: Import Options Configuration"""
    event = get_object_or_404(Event, id=event_id)
    bulk_upload = get_object_or_404(BulkRegistrationUpload, id=upload_id, event=event)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to manage this event.')
        return redirect('organizer_event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = ImportOptionsForm(request.POST, event=event)
        if form.is_valid():
            # Save import options
            options = bulk_upload.import_options or {}
            options.update({
                'duplicate_handling': form.cleaned_data['duplicate_handling'],
                'ticket_assignment_mode': form.cleaned_data['ticket_assignment_mode'],
                'send_emails': form.cleaned_data['send_emails'],
            })
            
            bulk_upload.import_options = options
            bulk_upload.default_ticket_type = form.cleaned_data['default_ticket_type']
            bulk_upload.current_step = 'configured'
            bulk_upload.save()
            
            # Log audit
            service = BulkRegistrationService(bulk_upload)
            service._log_audit('configuration', options, 'Import options configured')
            
            messages.success(request, 'Import options saved successfully!')
            return redirect('registration:bulk_wizard_execute', event_id=event.id, upload_id=bulk_upload.id)
    else:
        # Pre-populate form with existing options
        initial_data = bulk_upload.import_options or {}
        if bulk_upload.default_ticket_type:
            initial_data['default_ticket_type'] = bulk_upload.default_ticket_type
        
        form = ImportOptionsForm(initial=initial_data, event=event)
    
    return render(request, 'registration/bulk_wizard_options.html', {
        'event': event,
        'bulk_upload': bulk_upload,
        'form': form,
        'step': 4,
        'step_title': 'Configure Options'
    })


@login_required
def bulk_registration_wizard_execute(request, event_id, upload_id):
    """Step 5: Execute Import"""
    event = get_object_or_404(Event, id=event_id)
    bulk_upload = get_object_or_404(BulkRegistrationUpload, id=upload_id, event=event)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to manage this event.')
        return redirect('organizer_event_detail', event_id=event.id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'execute':
            try:
                service = BulkRegistrationService(bulk_upload)
                results = service.execute_import()
                
                messages.success(request, 
                    f'Import completed! {results["success"]} registrations created, '
                    f'{results["skipped"]} skipped, {results["failed"]} failed.')
                
                return redirect('registration:bulk_wizard_results', event_id=event.id, upload_id=bulk_upload.id)
                
            except Exception as e:
                messages.error(request, f'Import failed: {str(e)}')
        elif action == 'back_to_options':
            return redirect('registration:bulk_wizard_options', event_id=event.id, upload_id=bulk_upload.id)
    
    # Calculate import preview
    processable_rows = bulk_upload.rows.filter(
        validation_status__in=['valid', 'warning']
    ).count()
    
    duplicate_count = bulk_upload.rows.filter(is_duplicate=True).count()
    
    return render(request, 'registration/bulk_wizard_execute.html', {
        'event': event,
        'bulk_upload': bulk_upload,
        'processable_rows': processable_rows,
        'duplicate_count': duplicate_count,
        'step': 5,
        'step_title': 'Execute Import'
    })


@login_required
def bulk_registration_wizard_results(request, event_id, upload_id):
    """Step 6: View Results"""
    event = get_object_or_404(Event, id=event_id)
    bulk_upload = get_object_or_404(BulkRegistrationUpload, id=upload_id, event=event)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to manage this event.')
        return redirect('organizer_event_detail', event_id=event.id)
    
    # Get audit logs
    audit_logs = bulk_upload.audit_logs.order_by('-performed_at')[:10]
    
    # Get processing results
    success_rows = bulk_upload.rows.filter(status='success').count()
    skipped_rows = bulk_upload.rows.filter(status='skipped').count()
    failed_rows = bulk_upload.rows.filter(status='failed').count()
    
    return render(request, 'registration/bulk_wizard_results.html', {
        'event': event,
        'bulk_upload': bulk_upload,
        'audit_logs': audit_logs,
        'success_rows': success_rows,
        'skipped_rows': skipped_rows,
        'failed_rows': failed_rows,
        'step': 6,
        'step_title': 'Import Results'
    })


@login_required
def download_error_report(request, event_id, upload_id):
    """Download error report as CSV"""
    event = get_object_or_404(Event, id=event_id)
    bulk_upload = get_object_or_404(BulkRegistrationUpload, id=upload_id, event=event)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this report.')
        return redirect('organizer_event_detail', event_id=event.id)
    
    service = BulkRegistrationService(bulk_upload)
    csv_content = service.generate_error_report()
    
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bulk_import_errors_{bulk_upload.id}.csv"'
    
    return response


@login_required
def download_template(request, event_id):
    """Download CSV template with event-specific fields"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this template.')
        return redirect('organizer_event_detail', event_id=event.id)
    
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Standard columns
    headers = ['Full Name', 'Email Address', 'Phone Number', 'Company', 'Job Title']
    
    # Add ticket types as options
    ticket_types = event.ticket_types.filter(is_active=True)
    if ticket_types.exists():
        headers.append('Ticket Type')
    
    # Add custom fields
    custom_fields = event.registration_fields.filter(is_active=True).order_by('order')
    for field in custom_fields:
        headers.append(field.label)
    
    writer.writerow(headers)
    
    # Add sample data row
    sample_row = ['John Doe', 'john.doe@example.com', '+1234567890', 'Acme Inc', 'Developer']
    
    if ticket_types.exists():
        sample_row.append(ticket_types.first().name)
    
    for field in custom_fields:
        if field.field_type == 'select':
            options = field.get_options_list()
            sample_row.append(options[0] if options else 'Sample Value')
        else:
            sample_row.append('Sample Value')
    
    writer.writerow(sample_row)
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bulk_registration_template_{event.id}.csv"'
    
    return response


@login_required
@require_http_methods(["GET"])
def ajax_validation_preview(request, event_id, upload_id):
    """AJAX endpoint for validation preview data"""
    event = get_object_or_404(Event, id=event_id)
    bulk_upload = get_object_or_404(BulkRegistrationUpload, id=upload_id, event=event)
    
    # Check permissions
    if event.organizer != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get filtered rows
    status_filter = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    per_page = 20
    
    rows_queryset = bulk_upload.rows.order_by('row_number')
    
    if status_filter != 'all':
        rows_queryset = rows_queryset.filter(validation_status=status_filter)
    
    if search:
        rows_queryset = rows_queryset.filter(mapped_data__icontains=search)
    
    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    rows = rows_queryset[start:end]
    
    # Format data
    data = []
    for row in rows:
        mapped_data = row.mapped_data or {}
        data.append({
            'row_number': row.row_number,
            'validation_status': row.validation_status,
            'attendee_name': mapped_data.get('attendee_name', ''),
            'attendee_email': mapped_data.get('attendee_email', ''),
            'attendee_phone': mapped_data.get('attendee_phone', ''),
            'company': mapped_data.get('company', ''),
            'validation_errors': row.validation_errors or [],
            'validation_warnings': row.validation_warnings or [],
            'is_duplicate': row.is_duplicate,
        })
    
    return JsonResponse({
        'rows': data,
        'has_more': rows_queryset.count() > end,
        'total_count': rows_queryset.count()
    })