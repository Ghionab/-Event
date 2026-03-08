from django import forms
from .models import BusinessSponsor, Expense, Budget, Invoice, Quote, Report


class SponsorForm(forms.ModelForm):
    class Meta:
        model = BusinessSponsor
        fields = [
            'company_name', 'contact_name', 'contact_email', 'contact_phone',
            'tier', 'description', 'website', 'logo', 'booth_number',
            'booth_location', 'booth_size', 'benefits', 'sponsorship_amount',
            'payment_status', 'payment_notes', 'is_confirmed'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'benefits': forms.Textarea(attrs={'rows': 3}),
            'payment_notes': forms.Textarea(attrs={'rows': 2}),
            'booth_location': forms.Textarea(attrs={'rows': 2}),
        }


class SponsorLeadForm(forms.ModelForm):
    class Meta:
        model = BusinessSponsor
        fields = ['company_name', 'contact_name', 'contact_email', 'contact_phone']
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': 'Company Name'}),
            'contact_name': forms.TextInput(attrs={'placeholder': 'Contact Name'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': 'Phone'}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'vendor', 'amount', 'expense_date', 'due_date', 'payment_status', 'receipt', 'notes']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': 'Expense description'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'planned_amount', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client_name', 'client_email', 'client_address', 'description', 'amount', 'tax_rate', 'issue_date', 'due_date', 'status', 'notes']
        widgets = {
            'client_address': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['client_name', 'client_email', 'client_company', 'items', 'tax_rate', 'valid_until', 'notes']
        widgets = {
            'items': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Item 1: Description, Amount\nItem 2: Description, Amount'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['event', 'name', 'report_type', 'export_format', 'filters', 'is_scheduled', 'schedule_frequency']
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Report name'}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'export_format': forms.Select(attrs={'class': 'form-control'}),
            'filters': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '{"status": "confirmed"}'}),
            'is_scheduled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'schedule_frequency': forms.Select(attrs={'class': 'form-control'}),
        }


class ReportExportForm(forms.Form):
    format = forms.ChoiceField(
        choices=[('csv', 'CSV'), ('xlsx', 'Excel'), ('pdf', 'PDF')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )