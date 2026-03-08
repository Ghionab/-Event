from django import forms
from django.conf import settings
from .models import Registration, TicketType, PromoCode, RegistrationField, RegistrationDocument, ManualRegistration

class RegistrationForm(forms.ModelForm):
    promo_code = forms.CharField(required=False, max_length=50, help_text='Enter promo code if you have one')
    
    class Meta:
        model = Registration
        fields = ['ticket_type', 'attendee_name', 'attendee_email', 'attendee_phone', 'special_requests', 'promo_code']
        widgets = {
            'attendee_name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'attendee_email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'attendee_phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any special requests or dietary requirements?'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove promo_code from fields since we handle it separately
        self.fields.pop('promo_code', None)

class TicketTypeForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = ['name', 'description', 'ticket_category', 'price', 'quantity_available', 'sales_start', 'sales_end', 'benefits', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Describe this ticket type'}),
            'benefits': forms.Textarea(attrs={'rows': 2, 'placeholder': 'List benefits (one per line)'}),
            'sales_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'sales_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        fields = ['code', 'discount_type', 'discount_value', 'max_uses', 'max_uses_per_user', 'valid_from', 'valid_until', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'PROMO2024', 'style': 'text-transform: uppercase;'}),
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data['code'].upper()
        return code

class RegistrationFieldForm(forms.ModelForm):
    class Meta:
        model = RegistrationField
        fields = ['field_name', 'field_type', 'label', 'help_text', 'required', 'options', 'placeholder', 'order', 'is_active']
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'Field Label'}),
            'help_text': forms.TextInput(attrs={'placeholder': 'Help text for attendees'}),
            'placeholder': forms.TextInput(attrs={'placeholder': 'Placeholder text'}),
            'options': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Comma-separated options for dropdown/radio/checkbox'}),
        }
    
    def clean_field_name(self):
        import re
        field_name = self.cleaned_data['field_name'].lower()
        # Only allow alphanumeric and underscores
        if not re.match(r'^[a-z0-9_]+$'):
            raise forms.ValidationError('Field name can only contain lowercase letters, numbers, and underscores.')
        return field_name

class PromoCodeValidateForm(forms.Form):
    code = forms.CharField(max_length=50)
    event_id = forms.IntegerField()
    ticket_price = forms.DecimalField(max_digits=10, decimal_places=2)


class RegistrationDocumentForm(forms.ModelForm):
    """Form for uploading registration documents"""
    file = forms.FileField(
        help_text='Upload PDF, Excel, Word, or image files'
    )

    class Meta:
        model = RegistrationDocument
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError('Please upload a file.')

        # Check file size
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
        if file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(f'File size cannot exceed {max_mb}MB.')

        # Check file extension
        import os
        ext = os.path.splitext(file.name)[1].lower()
        allowed = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv',
            '.jpg', '.jpeg', '.png', '.gif', '.webp'
        ])

        if ext not in allowed:
            raise forms.ValidationError(
                f'File type not allowed. Allowed types: {", ".join(allowed)}'
            )

        # Check MIME type
        allowed_mimes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
        ]

        if file.content_type not in allowed_mimes:
            raise forms.ValidationError('File type not supported.')

        return file


class RegistrationFieldFormWithFile(forms.ModelForm):
    """Extended form with file upload options"""
    class Meta:
        model = RegistrationField
        fields = ['field_name', 'field_type', 'label', 'help_text', 'required', 'options', 'placeholder', 'validation_regex', 'min_value', 'max_value', 'order', 'is_active']
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'Field Label'}),
            'help_text': forms.TextInput(attrs={'placeholder': 'Help text for attendees'}),
            'placeholder': forms.TextInput(attrs={'placeholder': 'Placeholder text'}),
            'options': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'For dropdown/radio/checkbox: comma-separated values.\nFor file upload: comma-separated extensions (e.g., .pdf,.doc,.xlsx)'
            }),
            'validation_regex': forms.TextInput(attrs={'placeholder': 'Regular expression for validation'}),
            'min_value': forms.TextInput(attrs={'placeholder': 'Minimum value'}),
            'max_value': forms.TextInput(attrs={'placeholder': 'Maximum value'}),
        }

    def clean_field_name(self):
        import re
        field_name = self.cleaned_data['field_name'].lower()
        if not re.match(r'^[a-z0-9_]+$'):
            raise forms.ValidationError('Field name can only contain lowercase letters, numbers, and underscores.')
        return field_name

    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        options = cleaned_data.get('options')

        # For file upload fields, validate options
        if field_type == 'file':
            if options:
                # Validate file extensions
                extensions = [opt.strip().lower() for opt in options.split(',')]
                allowed = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', [])
                for ext in extensions:
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    if ext not in allowed:
                        raise forms.ValidationError(
                            f'Invalid file extension: {ext}. Allowed: {", ".join(allowed)}'
                        )
        return cleaned_data


# =============================================================================
# Bulk Registration Forms
# =============================================================================

class BulkUploadForm(forms.Form):
    """Form for bulk registration upload"""

    EXCEL = 'excel'
    CSV = 'csv'

    FILE_TYPE_CHOICES = [
        (EXCEL, 'Excel (.xlsx)'),
        (CSV, 'CSV (.csv)'),
    ]

    file_type = forms.ChoiceField(
        choices=FILE_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial=EXCEL,
        help_text="Select the format of your file"
    )

    file = forms.FileField(
        help_text='Upload Excel (.xlsx) or CSV file with attendee data'
    )

    skip_header = forms.BooleanField(
        required=False,
        initial=True,
        help_text='Check if first row contains headers'
    )

    send_invitations = forms.BooleanField(
        required=False,
        initial=True,
        help_text='Send invitation emails to registered attendees'
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('Please upload a file.')

        # Check file extension
        import os
        ext = os.path.splitext(file.name)[1].lower()

        allowed_extensions = ['.xlsx', '.xls', '.csv']
        if ext not in allowed_extensions:
            raise forms.ValidationError(
                f'File type not allowed. Please upload Excel (.xlsx, .xls) or CSV file.'
            )

        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if file.size > max_size:
            raise forms.ValidationError('File size cannot exceed 5MB.')

        return file


class ManualRegistrationForm(forms.ModelForm):
    """Form for manual registration entry"""

    class Meta:
        model = ManualRegistration
        fields = [
            'attendee_name', 'attendee_email', 'attendee_phone',
            'company', 'job_title', 'ticket_type', 'notes'
        ]
        widgets = {
            'attendee_name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'attendee_email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'attendee_phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'company': forms.TextInput(attrs={'placeholder': 'Company'}),
            'job_title': forms.TextInput(attrs={'placeholder': 'Job Title'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Additional notes'}),
        }

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['ticket_type'].queryset = event.ticket_types.filter(is_active=True)

    def clean_attendee_email(self):
        email = self.cleaned_data.get('attendee_email')
        event = self.initial.get('event')

        # Check if already registered
        if event:
            existing = Registration.objects.filter(
                event=event,
                attendee_email__iexact=email
            ).first()
            if existing:
                raise forms.ValidationError(
                    f'This email is already registered for this event.'
                )

        return email


class ManualRegistrationBulkForm(forms.Form):
    """Form for creating multiple manual registrations at once"""

    attendees_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 10,
            'placeholder': 'Enter attendee data (one per line):\nName, Email, Phone, Company, Job Title'
        }),
        help_text='Enter multiple attendees, one per line, comma-separated'
    )

    ticket_type = forms.ModelChoiceField(
        queryset=None,
        empty_label='Select Ticket Type',
        help_text='Ticket type to assign to all attendees'
    )

    send_invitations = forms.BooleanField(
        required=False,
        initial=True,
        help_text='Send invitation emails to all attendees'
    )

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['ticket_type'].queryset = event.ticket_types.filter(is_active=True)

    def clean_attendees_data(self):
        data = self.cleaned_data.get('attendees_data')
        if not data:
            return data

        lines = data.strip().split('\n')
        errors = []

        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 2:
                errors.append(f'Line {i}: Need at least name and email')

            # Validate email
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if len(parts) >= 2 and not re.match(email_pattern, parts[1]):
                errors.append(f'Line {i}: Invalid email address "{parts[1]}"')

        if errors:
            raise forms.ValidationError(errors)

        return data
