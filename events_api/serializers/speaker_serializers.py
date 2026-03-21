from rest_framework import serializers
from events.models import Speaker


class SpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = ['id', 'name', 'email', 'photo', 'bio', 'job_title', 'company',
                  'website', 'twitter', 'linkedin_url', 'facebook', 'instagram',
                  'youtube', 'is_confirmed', 'is_featured', 'display_order']
        read_only_fields = ['id']


class SpeakerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = ['name', 'email', 'photo', 'bio', 'job_title', 'company',
                  'website', 'twitter', 'linkedin_url', 'facebook', 'instagram',
                  'youtube', 'is_confirmed', 'is_featured', 'display_order']

    def create(self, validated_data):
        event_id = self.context.get('event_id')
        validated_data['event_id'] = event_id
        return super().create(validated_data)
