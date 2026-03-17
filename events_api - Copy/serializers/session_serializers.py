from rest_framework import serializers
from events.models import EventSession


class SessionSerializer(serializers.ModelSerializer):
    track_name = serializers.CharField(source='track.name', read_only=True, allow_null=True)

    class Meta:
        model = EventSession
        fields = ['id', 'title', 'description', 'start_time', 'end_time',
                  'location', 'track', 'track_name', 'capacity', 'registered_count',
                  'session_type', 'slides', 'recording_url', 'is_public', 'is_featured']


class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSession
        fields = ['title', 'description', 'start_time', 'end_time',
                  'location', 'track', 'capacity', 'session_type']

    def create(self, validated_data):
        event_id = self.context.get('event_id')
        validated_data['event_id'] = event_id
        return super().create(validated_data)
