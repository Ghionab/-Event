"""
Enterprise Bulk Registration Forms
"""
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from .models import BulkRegistrationUpload, TicketType, RegistrationField
import os


class BulkUploadWizardForm(forms.ModelForm):
    """Step 1: File Upload Form"""
    
    file = forms.FileField(
        validators=[
            FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls']),
        ],
        widget=forms.FileInput(attrs={
            'accept': '.csv,.xlsx,.xls',
            'class': 'hidden',
            'id': 'fileInput'
        }),
        help_text='Upload CSV (.csv) or Excel (.xlsx, .xls) files only. Maximum size: 20MB.'
    )
    
    skip_header = forms.BooleanField(
        required=False,
        initial=True,
        label='First row contains headers',
        help_text='Check if your file has column names in the first row'
    )
    
    class Meta:
        model = BulkRegistrationUpload
        fields = ['file', 'skip_header']
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            return file
            
        # Check file size (20MB limit)
        max_size = 20 * 1024 * 1024  # 20MB in bytes
        if file.size > max_size:
            raise ValidationError(f'File size ({file.size / (1024*1024):.1f}MB) exceeds maximum allowed size (20MB).')
        
        # Check file extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ['.csv', '.xlsx', '.xls']:
            raise ValidationError('Only CSV (.csv) and Excel (.xlsx, .xls) files are supported.')
        
        return file


class ColumnMappingForm(forms.Form):
    """Step 2: Column Mapping Form"""
    
    def __init__(self, *args, **kwargs):
        detected_columns = kwargs.pop('detected_columns', [])
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        # System field choices
        system_fields = [
            ('', '-- Select Field --'),
            ('attendee_name', 'Attendee Name (Required)'),
            ('attendee_email', 'Email Address (Required)'),
            ('attendee_phone', 'Phone Number'),
            ('company', 'Company/Organization'),
            ('job_title', 'Job Title'),
            ('ticket_type', 'Ticket Type'),
            ('ignore', 'Ignore Column'),
        ]
        
        # Add custom registration fields if event is provided
        if event:
            custom_fields = event.registration_fields.filter(is_active=True).order_by('order')
            for field in custom_fields:
                system_fields.append((f'custom_{field.id}', f'{field.label} (Custom)'))
        
        # Create mapping fields for each detected column
        for i, column in enumerate(detected_columns):
            field_name = f'mapping_{i}'
            
            # Auto-detect common column names
            auto_value = self._auto_detect_field(column)
            
            self.fields[field_name] = forms.ChoiceField(
                choices=system_fields,
                initial=auto_value,
                label=f'Map "{column}" to:',
                required=True,
                widget=forms.Select(attrs={
                    'class': 'form-select',
                    'data_column': column,
                })
            )
    
    def _auto_detect_field(self, column_name):
        """Auto-detect system field based on column name"""
        column_lower = column_name.lower().strip()
        
        # Name variations
        if any(name in column_lower for name in ['name', 'full_name', 'attendee_name', 'participant']):
            return 'attendee_name'
        
        # Email variations
        if any(email in column_lower for email in ['email', 'e-mail', 'mail', 'email_address']):
            return 'attendee_email'
        
        # Phone variations
        if any(phone in column_lower for phone in ['phone', 'telephone', 'mobile', 'cell', 'contact']):
            return 'attendee_phone'
        
        # Company variations
        if any(company in column_lower for company in ['company', 'organization', 'org', 'employer', 'business']):
            return 'company'
        
        # Job title variations
        if any(job in column_lower for job in ['job', 'title', 'position', 'role', 'designation']):
            return 'job_title'
        
        # Ticket type variations
        if any(ticket in column_lower for ticket in ['ticket', 'type', 'category', 'pass']):
            return 'ticket_type'
        
        return ''  # No auto-detection
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check that required fields are mapped
        mapped_fields = []
        required_fields = ['attendee_name', 'attendee_email']
        
        for field_name, value in cleaned_data.items():
            if field_name.startswith('mapping_') and value and value != 'ignore':
                mapped_fields.append(value)
        
        # Check for required fields
        for required_field in required_fields:
            if required_field not in mapped_fields:
                field_label = 'Attendee Name' if required_field == 'attendee_name' else 'Email Address'
                raise ValidationError(f'{field_label} is required and must be mapped to a column.')
        
        # Check for duplicate mappings (except 'ignore')
        non_ignore_fields = [f for f in mapped_fields if f != 'ignore']
        if len(non_ignore_fields) != len(set(non_ignore_fields)):
            raise ValidationError('Each system field can only be mapped to one column.')
        
        return cleaned_data


class ImportOptionsForm(forms.Form):
    """Step 4: Import Configuration Form"""
    
    DUPLICATE_CHOICES = [
        ('skip', 'Skip duplicates (recommended)'),
        ('update', 'Update existing registrations'),
        ('allow', 'Allow duplicates'),
    ]
    
    TICKET_ASSIGNMENT_CHOICES = [
        ('same_for_all', 'Assign same ticket type to all attendees'),
        ('per_row', 'Use ticket type from file (if mapped)'),
        ('default', 'Use default ticket type for unmapped rows'),
    ]
    
    duplicate_handling = forms.ChoiceField(
        choices=DUPLICATE_CHOICES,
        initial='skip',
        label='Duplicate Email Handling',
        help_text='How to handle attendees with email addresses that are already registered',
        widget=forms.RadioSelect
    )
    
    ticket_assignment_mode = forms.ChoiceField(
        choices=TICKET_ASSIGNMENT_CHOICES,
        initial='same_for_all',
        label='Ticket Assignment',
        help_text='How to assign ticket types to imported attendees',
        widget=forms.RadioSelect
    )
    
    default_ticket_type = forms.ModelChoiceField(
        queryset=TicketType.objects.none(),
        required=False,
        label='Default Ticket Type',
        help_text='Ticket type to assign when not specified in file',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    send_emails = forms.BooleanField(
        required=False,
        initial=True,
        label='Send confirmation emails',
        help_text='Send registration confirmation emails to all imported attendees'
    )
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        if event:
            self.fields['default_ticket_type'].queryset = event.ticket_types.filter(
                is_active=True
            ).order_by('price')
    
    def clean(self):
        cleaned_data = super().clean()
        ticket_mode = cleaned_data.get('ticket_assignment_mode')
        default_ticket = cleaned_data.get('default_ticket_type')
        
        if ticket_mode in ['same_for_all', 'default'] and not default_ticket:
            raise ValidationError('Default ticket type is required for the selected assignment mode.')
        
        return cleaned_data


class ValidationFilterForm(forms.Form):
    """Form for filtering validation results"""
    
    STATUS_CHOICES = [
        ('all', 'All Rows'),
        ('valid', 'Valid Only'),
        ('warning', 'Warnings Only'),
        ('error', 'Errors Only'),
    ]
    
    status_filter = forms.ChoiceField(
        choices=STATUS_CHOICES,
        initial='all',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'onchange': 'filterRows(this.value)'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Search by name or email...',
            'onkeyup': 'searchRows(this.value)'
        })
    )