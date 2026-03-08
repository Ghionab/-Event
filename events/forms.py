from django import forms
from .models import Event, EventSession, Speaker, Track, Room, Sponsor

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'status', 'start_date', 'end_date',
            'registration_deadline', 'venue_name', 'address', 'city', 'country',
            'virtual_meeting_url', 'virtual_platform', 'logo', 'banner_image',
            'primary_color', 'secondary_color', 'max_attendees', 'is_public',
            'require_approval', 'meta_title', 'meta_description', 'contact_email',
            'contact_phone'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

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
                  'website', 'twitter', 'linkedin', 'facebook', 'instagram',
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
