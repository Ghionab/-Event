from rest_framework import serializers
from events.models import Event, Track, Room, Sponsor
from events_api.serializers.session_serializers import DynamicSessionSerializer, SessionWithSpeakersSerializer
from events_api.serializers.speaker_serializers import SpeakerSerializer


class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ['id', 'name', 'description', 'color', 'order']


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name', 'description', 'capacity', 'floor', 'building', 'virtual_url', 'virtual_platform']


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsor
        fields = ['id', 'company_name', 'logo', 'website', 'description', 'tier',
                  'contact_name', 'contact_email', 'is_featured', 'display_order']


class EventSerializer(serializers.ModelSerializer):
    tracks = TrackSerializer(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    sponsors = SponsorSerializer(many=True, read_only=True)
    sessions = serializers.SerializerMethodField()
    dynamic_sessions = DynamicSessionSerializer(many=True, read_only=True)
    speakers = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    theme_css = serializers.CharField(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'slug', 'description', 'event_type', 'status',
                  'start_date', 'end_date', 'registration_deadline',
                  'venue_name', 'address', 'city', 'country',
                  'virtual_meeting_url', 'virtual_platform',
                  'logo', 'banner_image', 'primary_color', 'secondary_color',
                  'accent_color', 'background_color', 'theme_css',
                  'max_attendees', 'is_public', 'require_approval',
                  'contact_email', 'contact_phone',
                  'tracks', 'rooms', 'sponsors', 'sessions', 'dynamic_sessions', 'speakers', 'is_owner']
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_sessions(self, obj):
        """Get event sessions with speakers"""
        sessions = obj.sessions.filter(is_public=True).order_by('start_time')
        return SessionWithSpeakersSerializer(sessions, many=True).data
    
    def get_speakers(self, obj):
        """Get confirmed speakers for the event"""
        speakers = obj.speakers.filter(is_confirmed=True).order_by('display_order', 'name')
        return SpeakerSerializer(speakers, many=True).data

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request and request.user.is_authenticated and obj.organizer == request.user


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type',
                  'start_date', 'end_date', 'registration_deadline',
                  'venue_name', 'address', 'city', 'country',
                  'virtual_meeting_url', 'virtual_platform',
                  'primary_color', 'secondary_color', 'accent_color', 'background_color',
                  'max_attendees', 'is_public', 'require_approval',
                  'contact_email', 'contact_phone']

    def create(self, validated_data):
        validated_data['organizer'] = self.context['request'].user
        validated_data['status'] = 'draft'  # Auto-assign draft status
        return super().create(validated_data)


class EventListSerializer(serializers.ModelSerializer):
    """Serializer for event list with pricing information"""
    price_display = serializers.SerializerMethodField()
    is_free = serializers.SerializerMethodField()
    has_tickets = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'slug', 'event_type', 'status',
                  'start_date', 'end_date', 'venue_name', 'city',
                  'logo', 'primary_color', 'secondary_color', 'accent_color', 'background_color',
                  'is_public', 'price_display', 'is_free', 'has_tickets']
    
    def get_price_display(self, obj):
        """Return price range or status for display on browse page"""
        ticket_types = obj.ticket_types.filter(is_active=True)
        
        if not ticket_types.exists():
            return None  # No tickets available
        
        prices = [tt.price for tt in ticket_types if tt.price is not None]
        
        if not prices:
            return None
        
        min_price = min(prices)
        max_price = max(prices)
        
        if min_price == 0 and max_price == 0:
            return 'Free'
        elif min_price == max_price:
            return f'${min_price:.2f}'
        else:
            return f'From ${min_price:.2f}'
    
    def get_is_free(self, obj):
        """Check if event is truly free (has tickets and all are free)"""
        ticket_types = obj.ticket_types.filter(is_active=True)
        
        if not ticket_types.exists():
            return False  # No tickets = not a free event
        
        # All ticket types must have price=0 to be considered free
        return all(tt.price == 0 for tt in ticket_types)
    
    def get_has_tickets(self, obj):
        """Check if event has any active tickets"""
        return obj.ticket_types.filter(is_active=True).exists()
