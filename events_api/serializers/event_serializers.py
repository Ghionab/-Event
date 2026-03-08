from rest_framework import serializers
from events.models import Event, Track, Room, Sponsor


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
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'title', 'slug', 'description', 'event_type', 'status',
                  'start_date', 'end_date', 'registration_deadline',
                  'venue_name', 'address', 'city', 'country',
                  'virtual_meeting_url', 'virtual_platform',
                  'primary_color', 'secondary_color',
                  'max_attendees', 'is_public', 'require_approval',
                  'contact_email', 'contact_phone',
                  'tracks', 'rooms', 'sponsors', 'is_owner']
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request and request.user.is_authenticated and obj.organizer == request.user


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'status',
                  'start_date', 'end_date', 'registration_deadline',
                  'venue_name', 'address', 'city', 'country',
                  'virtual_meeting_url', 'virtual_platform',
                  'primary_color', 'secondary_color',
                  'max_attendees', 'is_public', 'require_approval',
                  'contact_email', 'contact_phone']

    def create(self, validated_data):
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)


class EventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'slug', 'event_type', 'status',
                  'start_date', 'end_date', 'venue_name', 'city',
                  'primary_color', 'is_public']
