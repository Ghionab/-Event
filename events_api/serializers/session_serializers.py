from rest_framework import serializers
from events.models import EventSession, Session, SessionSpeaker


class SessionSpeakerSerializer(serializers.ModelSerializer):
    """Serializer for individual speakers within a session"""
    class Meta:
        model = SessionSpeaker
        fields = ['id', 'speaker_name', 'speaker_bio', 'speaker_profile_picture',
                  'speaker_linkedin_url', 'speaker_start_time', 'speaker_end_time', 'display_order']


class DynamicSessionSerializer(serializers.ModelSerializer):
    """Serializer for dynamic sessions with their speakers"""
    session_speakers = SessionSpeakerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Session
        fields = ['id', 'title', 'speaker_name', 'speaker_profile_picture', 'speaker_bio',
                  'session_start_time', 'session_end_time', 'speaker_start_time', 'speaker_end_time',
                  'session_speakers']


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


class SessionWithSpeakersSerializer(serializers.ModelSerializer):
    """EventSession with related speakers data"""
    track_name = serializers.CharField(source='track.name', read_only=True, allow_null=True)
    speakers = serializers.SerializerMethodField()
    
    class Meta:
        model = EventSession
        fields = ['id', 'title', 'description', 'start_time', 'end_time',
                  'location', 'track', 'track_name', 'capacity', 'registered_count',
                  'session_type', 'slides', 'recording_url', 'is_public', 'is_featured', 'speakers']
    
    def get_speakers(self, obj):
        """Get speakers for this session"""
        speakers = obj.speakers.filter(is_confirmed=True).order_by('display_order', 'name')
        from events_api.serializers.speaker_serializers import SpeakerSerializer
        return SpeakerSerializer(speakers, many=True).data
