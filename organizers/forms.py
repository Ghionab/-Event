from django import forms
from .models import OrganizerProfile, EventTemplate, OrganizerTeamMember


class OrganizerProfileForm(forms.ModelForm):
    class Meta:
        model = OrganizerProfile
        fields = [
            'company_name', 'company_description', 'logo', 'website', 'phone',
            'address', 'city', 'country', 'facebook_url', 'twitter_handle',
            'linkedin_url', 'instagram_handle'
        ]
        widgets = {
            'company_description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class EventTemplateForm(forms.ModelForm):
    default_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False
    )
    session_template = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        required=False
    )

    class Meta:
        model = EventTemplate
        fields = ['name', 'description', 'event_type', 'default_description',
                  'session_template', 'default_primary_color', 'default_secondary_color', 'is_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class TeamMemberInviteForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = OrganizerTeamMember
        fields = ['email', 'role', 'permissions']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['permissions'].widget = forms.Textarea(attrs={
            'placeholder': 'Enter permissions as JSON, e.g., {"manage_events": true, "view_analytics": true}'
        })