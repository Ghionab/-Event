from django import forms
from django.forms import inlineformset_factory
from .models import Event, EventSession, Speaker, Track, Room, Sponsor, Session, SessionSpeaker

class EventForm(forms.ModelForm):
    # Email invitation field (not part of the model)
    invite_emails = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Enter email addresses separated by commas or new lines'
        }),
        help_text='Optional: Send event invitations to these email addresses',
        label='Invite via Email'
    )
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'start_date', 'end_date',
            'venue_name', 'city', 'country', 'logo', 'banner_image',
            'max_attendees', 'is_public'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Surgical fix: If editing an existing event, make fields optional if they are not in the UI
        # This prevents validation errors for hidden fields that might be required in the model
        if self.instance and self.instance.pk:
            ui_fields = [
                'title', 'description', 'event_type', 'start_date', 'end_date',
                'venue_name', 'address', 'city', 'country', 'virtual_meeting_url',
                'primary_color', 'secondary_color', 'max_attendees', 'is_public'
            ]
            for field_name in self.fields:
                if field_name not in ui_fields:
                    self.fields[field_name].required = False
                    
        # Ensure status is set to published by default if we were to handle it here
        # (Though it's already handled in the model default)
    
    def clean_invite_emails(self):
        """Validate and parse email addresses"""
        emails_text = self.cleaned_data.get('invite_emails', '').strip()
        if not emails_text:
            return []
        
        # Split by comma or newline
        import re
        email_list = re.split(r'[,\n]+', emails_text)
        
        # Clean and validate each email
        cleaned_emails = []
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        for email in email_list:
            email = email.strip()
            if email:
                try:
                    validate_email(email)
                    cleaned_emails.append(email)
                except DjangoValidationError:
                    raise forms.ValidationError(f'Invalid email address: {email}')
        
        return cleaned_emails

class EventSessionForm(forms.ModelForm):
    class Meta:
        model = EventSession
        fields = ['title', 'description', 'start_time', 'end_time', 'location', 
                  'track', 'capacity', 'session_type', 'slides', 'recording_url',
                  'resources', 'tags', 'is_public', 'is_featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'resources': forms.Textarea(attrs={'rows': 2, 'placeholder': 'One URL per line'}),
        }
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['track'].queryset = Track.objects.filter(event=event)

class SpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = ['name', 'email', 'photo', 'bio', 'job_title', 'company', 
                  'website', 'twitter', 'linkedin_url', 'facebook', 'instagram',
                  'youtube', 'is_confirmed', 'is_featured', 'display_order']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class TrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = ['name', 'description', 'color', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'description', 'capacity', 'floor', 'building',
                  'virtual_url', 'virtual_platform', 'amenities', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'amenities': forms.Textarea(attrs={'rows': 2, 'placeholder': 'One amenity per line'}),
        }
    
    def clean_amenities(self):
        amenities = self.cleaned_data['amenities']
        if isinstance(amenities, str):
            return [a.strip() for a in amenities.split('\n') if a.strip()]
        return amenities

class SponsorForm(forms.ModelForm):
    class Meta:
        model = Sponsor
        fields = ['company_name', 'logo', 'website', 'description', 'tier',
                  'contact_name', 'contact_email', 'contact_phone', 'booth_number',
                  'booth_description', 'promotional_url', 'promotional_video',
                  'display_order', 'is_featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'booth_description': forms.Textarea(attrs={'rows': 2}),
        }

class SpeakerSessionAssignmentForm(forms.Form):
    """Form to assign speakers to a session"""
    speakers = forms.ModelMultipleChoiceField(
        queryset=Speaker.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['speakers'].queryset = Speaker.objects.filter(event=event)
            if session:
                self.fields['speakers'].initial = session.speakers.all()


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['title', 'speaker_name', 'speaker_profile_picture', 'speaker_bio',
                  'session_start_time', 'session_end_time', 'speaker_start_time', 'speaker_end_time']
        widgets = {
            'speaker_bio': forms.Textarea(attrs={'rows': 2}),
            'session_start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'session_end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'speaker_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'speaker_end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all speaker-related fields optional in the form
        self.fields['speaker_name'].required = False
        self.fields['speaker_bio'].required = False
        self.fields['speaker_profile_picture'].required = False
        self.fields['session_start_time'].required = False
        self.fields['session_end_time'].required = False
        self.fields['speaker_start_time'].required = False
        self.fields['speaker_end_time'].required = False
        
        # Add help text for optional fields
        self.fields['speaker_name'].help_text = 'Optional: Primary speaker for this session'
        self.fields['speaker_bio'].help_text = 'Optional: Brief biography of the speaker'
        self.fields['speaker_profile_picture'].help_text = 'Optional: Speaker profile image'
        self.fields['session_start_time'].help_text = 'Optional: Session start date and time'
        self.fields['session_end_time'].help_text = 'Optional: Session end date and time'
        self.fields['speaker_start_time'].help_text = "Optional: Primary speaker's start time (HH:MM)"
        self.fields['speaker_end_time'].help_text = "Optional: Primary speaker's end time (HH:MM)"


class SessionSpeakerForm(forms.ModelForm):
    """Form for adding individual speakers to a session"""
    class Meta:
        model = SessionSpeaker
        fields = ['speaker_name', 'speaker_bio', 'speaker_profile_picture', 
                  'speaker_linkedin_url', 'speaker_start_time', 'speaker_end_time']
        widgets = {
            'speaker_bio': forms.Textarea(attrs={'rows': 2}),
            'speaker_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'speaker_end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field in self.fields.values():
            field.required = False
        
        # Add help text
        self.fields['speaker_name'].help_text = 'Optional: Speaker name'
        self.fields['speaker_bio'].help_text = 'Optional: Speaker biography'
        self.fields['speaker_profile_picture'].help_text = 'Optional: Profile picture'
        self.fields['speaker_start_time'].help_text = 'Optional: Speaker start time (HH:MM)'
        self.fields['speaker_end_time'].help_text = 'Optional: Speaker end time (HH:MM)'


SessionFormSet = inlineformset_factory(
    Event, 
    Session, 
    form=SessionForm, 
    extra=0, 
    can_delete=True
)

# Formset for managing speakers within a session
SessionSpeakerFormSet = inlineformset_factory(
    Session,
    SessionSpeaker,
    form=SessionSpeakerForm,
    extra=1,
    can_delete=True
)
