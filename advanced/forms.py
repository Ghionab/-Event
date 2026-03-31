from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Vendor, VendorContact, Contract, VendorPayment,
    TeamMember, Task, TaskComment, TeamNotification,
    AuditLog, DataExport, PrivacySetting, SecurityEvent
)
from events.models import Event

User = get_user_model()


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'name', 'category', 'contact_name', 'email', 'phone',
            'website', 'address', 'description', 'hourly_rate',
            'flat_rate', 'is_preferred', 'is_blacklisted'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'flat_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_preferred': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_blacklisted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VendorContactForm(forms.ModelForm):
    class Meta:
        model = VendorContact
        fields = ['event', 'contact_type', 'notes', 'follow_up_date']
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'contact_type': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'title', 'description', 'amount', 'payment_terms',
            'start_date', 'end_date', 'contract_file'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class VendorPaymentForm(forms.ModelForm):
    class Meta:
        model = VendorPayment
        fields = ['amount', 'description', 'due_date', 'invoice_number', 'receipt']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
        }


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = [
            'event', 'user', 'role', 'department', 'can_manage_registrations',
            'can_manage_sessions', 'can_manage_sponsors', 'can_view_financials',
            'can_manage_team', 'shift_start', 'shift_end', 'is_active'
        ]
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'shift_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'shift_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter events by organizer
        if user and not user.is_staff:
            self.fields['event'].queryset = Event.objects.filter(organizer=user)


class TeamMemberCreateForm(forms.Form):
    """Form for creating a new team member with user account"""
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Enter full name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Enter email address'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Enter password'
        })
    )
    
    role = forms.ChoiceField(
        choices=[
            ('coordinator', 'Coordinator'),
            ('organizer', 'Organizer')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def save(self, request, event=None):
        """Create user account and team member"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Create user account
        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['full_name'].split()[0] if ' ' in self.cleaned_data['full_name'] else self.cleaned_data['full_name'],
            last_name=' '.join(self.cleaned_data['full_name'].split()[1:]) if ' ' in self.cleaned_data['full_name'] else '',
            role=self.cleaned_data['role']
        )
        
        # Get event from request or use provided event
        if not event:
            from events.models import Event
            # Try to get an event from the current user
            event = Event.objects.filter(organizer=request.user).first()
        
        team_member = TeamMember.objects.create(
            user=user,
            event=event,
            role=self.cleaned_data['role'],
            is_active=True
        )
        
        return team_member


class TeamMemberUpdateForm(forms.Form):
    """Form for updating an existing team member"""
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Enter full name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Enter email address'
        })
    )
    
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Enter new password (optional)'
        })
    )
    
    role = forms.ChoiceField(
        choices=[
            ('coordinator', 'Coordinator'),
            ('organizer', 'Organizer')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.team_member = kwargs.pop('team_member', None)
        super().__init__(*args, **kwargs)
        
        if self.team_member:
            self.fields['full_name'].initial = self.team_member.user.get_full_name()
            self.fields['email'].initial = self.team_member.user.email
            self.fields['role'].initial = self.team_member.role
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.team_member and User.objects.filter(email=email).exclude(id=self.team_member.user.id).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def save(self):
        """Update user account and team member"""
        user = self.team_member.user
        
        # Update user details
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['full_name'].split()[0] if ' ' in self.cleaned_data['full_name'] else self.cleaned_data['full_name']
        user.last_name = ' '.join(self.cleaned_data['full_name'].split()[1:]) if ' ' in self.cleaned_data['full_name'] else ''
        
        # Update password if provided
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        
        user.save()
        
        # Update team member
        self.team_member.role = self.cleaned_data['role']
        self.team_member.save()
        
        return self.team_member


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'event', 'title', 'description', 'assigned_to', 'status',
            'priority', 'due_date', 'depends_on', 'tags',
            'progress_percentage', 'estimated_hours', 'actual_hours',
            'attachment', 'notes'
        ]
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'depends_on': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated tags'}),
            'progress_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'actual_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter events by organizer
        if user and not user.is_staff:
            self.fields['event'].queryset = Event.objects.filter(organizer=user)
        
        if event:
            # Filter assigned_to by event team members
            self.fields['assigned_to'].queryset = TeamMember.objects.filter(event=event, is_active=True)
            # Filter depends_on by event tasks
            self.fields['depends_on'].queryset = Task.objects.filter(event=event).exclude(
                pk=self.instance.pk if self.instance.pk else None
            )
            # Set event as initial value
            self.fields['event'].initial = event


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AuditLogFilterForm(forms.Form):
    action = forms.ChoiceField(
        choices=[('', 'All')] + list(AuditLog.ACTION_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    user = forms.ChoiceField(
        choices=[('', 'All Users')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class PrivacySettingForm(forms.ModelForm):
    class Meta:
        model = PrivacySetting
        fields = [
            'share_with_sponsors', 'share_with_speakers',
            'marketing_emails', 'event_updates',
            'retain_registration_history', 'retain_session_attendance',
            'allow_analytics'
        ]
        widgets = {
            'share_with_sponsors': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'share_with_speakers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'marketing_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'event_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'retain_registration_history': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'retain_session_attendance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_analytics': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }