from django import forms
from .models import EmailTemplate, ScheduledEmail, LivePoll, LiveQA


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'template_type', 'subject', 'html_content', 'text_content', 'available_variables', 'is_active']
        widgets = {
            'html_content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'text_content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'available_variables': forms.Textarea(attrs={'rows': 3, 'placeholder': 'user_name, event_title, event_date, etc.'}),
        }


class ScheduledEmailForm(forms.ModelForm):
    class Meta:
        model = ScheduledEmail
        fields = ['event', 'template', 'subject', 'content', 'recipient_filter', 'frequency', 'scheduled_at', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
            'recipient_filter': forms.Textarea(attrs={'rows': 3, 'placeholder': '{"status": "confirmed"}'}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class LivePollForm(forms.ModelForm):
    class Meta:
        model = LivePoll
        fields = ['event', 'session', 'question', 'poll_type', 'options', 'is_active', 'show_results_live', 'starts_at', 'ends_at']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 2}),
            'options': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Option 1\nOption 2\nOption 3'}),
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class LiveQAForm(forms.ModelForm):
    class Meta:
        model = LiveQA
        fields = ['question']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ask a question...'}),
        }


class PollResponseForm(forms.Form):
    selected_options = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=False)
    rating_value = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        required=False
    )
    wordcloud_response = forms.CharField(max_length=100, required=False)