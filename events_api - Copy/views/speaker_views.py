from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from events.models import Speaker
from events_api.serializers import SpeakerSerializer, SpeakerCreateSerializer
from events_api.permissions import IsOrganizer


class SpeakerViewSet(viewsets.ModelViewSet):
    serializer_class = SpeakerSerializer
    permission_classes = [IsOrganizer]

    def get_queryset(self):
        event_id = self.kwargs.get('event_pk')
        return Speaker.objects.filter(event_id=event_id)

    def get_serializer_class(self):
        if self.action == 'create':
            return SpeakerCreateSerializer
        return SpeakerSerializer

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_pk')
        serializer.save(event_id=event_id)

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None, event_pk=None):
        speaker = self.get_object()
        sessions = speaker.sessions.all()
        from events_api.serializers import SessionSerializer
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)
