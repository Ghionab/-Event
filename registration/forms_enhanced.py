from django import forms
from django.contrib.auth import get_user_model
from .models import TicketPurchase, Ticket, TicketAnswer, TicketType, RegistrationField

User = get_user_model()


class TicketPurchaseForm(forms.ModelForm):
    """Form for creating a ticket purchase"""
    promo_code = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter promo code',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    
    class Meta:
        model = TicketPurchase
        fields = ['promo_code']


class AttendeeInfoForm(forms.Form):
    """Form for individual attendee information"""
    attendee_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Full Name',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    attendee_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'email@example.com',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    attendee_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+1 234 567 8900',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    ticket_type_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        auto_fill = kwargs.pop('auto_fill', False)
        super().__init__(*args, **kwargs)
        
        # Auto-fill from user profile if logged in and auto_fill is True
        if user and user.is_authenticated and auto_fill:
            self.fields['attendee_name'].initial = user.get_full_name() or user.email
            self.fields['attendee_email'].initial = user.email
            # Try to get phone from user profile if available
            if hasattr(user, 'phone'):
                self.fields['attendee_phone'].initial = user.phone


class MultipleAttendeeFormSet(forms.BaseFormSet):
    """Formset for handling multiple attendees"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
    
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['user'] = self.user
        # Auto-fill only the first form
        kwargs['auto_fill'] = (index == 0)
        return kwargs


class CustomQuestionForm(forms.Form):
    """Dynamic form for custom registration questions"""
    
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', [])
        super().__init__(*args, **kwargs)
        
        for question in questions:
            field_name = f'question_{question.id}'
            
            if question.field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    widget=forms.TextInput(attrs={
                        'placeholder': question.placeholder,
                        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
                    })
                )
            
            elif question.field_type == 'textarea':
                self.fields[field_name] = forms.CharField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    widget=forms.Textarea(attrs={
                        'placeholder': question.placeholder,
                        'rows': 3,
                        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
                    })
                )
            
            elif question.field_type == 'number':
                self.fields[field_name] = forms.IntegerField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    widget=forms.NumberInput(attrs={
                        'placeholder': question.placeholder,
                        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
                    })
                )
            
            elif question.field_type == 'email':
                self.fields[field_name] = forms.EmailField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    widget=forms.EmailInput(attrs={
                        'placeholder': question.placeholder,
                        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
                    })
                )
            
            elif question.field_type == 'phone':
                self.fields[field_name] = forms.CharField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    widget=forms.TextInput(attrs={
                        'placeholder': question.placeholder,
                        'type': 'tel',
                        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
                    })
                )
            
            elif question.field_type == 'date':
                self.fields[field_name] = forms.DateField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    widget=forms.DateInput(attrs={
                        'type': 'date',
                        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
                    })
                )
            
            elif question.field_type == 'select':
                choices = [('', '-- Select --')] + [(opt, opt) for opt in question.get_options_list()]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    choices=choices,
                    widget=forms.Select(attrs={
                        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
                    })
                )
            
            elif question.field_type == 'radio':
                choices = [(opt, opt) for opt in question.get_options_list()]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={
                        'class': 'form-radio'
                    })
                )
            
            elif question.field_type == 'checkbox':
                self.fields[field_name] = forms.BooleanField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'form-checkbox'
                    })
                )
            
            elif question.field_type == 'file':
                self.fields[field_name] = forms.FileField(
                    label=question.label,
                    required=question.required,
                    help_text=question.help_text,
                    widget=forms.FileInput(attrs={
                        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
                    })
                )
