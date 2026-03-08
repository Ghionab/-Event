from django import forms
from .models import (
    Vendor, VendorContact, Contract, VendorPayment,
    TeamMember, Task, TaskComment, TeamNotification,
    AuditLog, DataExport, PrivacySetting, SecurityEvent
)


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
            'user', 'role', 'department', 'can_manage_registrations',
            'can_manage_sessions', 'can_manage_sponsors', 'can_view_financials',
            'can_manage_team', 'shift_start', 'shift_end', 'is_active'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'shift_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'shift_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'status',
            'priority', 'due_date', 'depends_on'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'depends_on': forms.Select(attrs={'class': 'form-control'}),
        }


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