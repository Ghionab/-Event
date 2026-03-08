from rest_framework import viewsets

from events.models import EventSession
from events_api.serializers import SessionSerializer, SessionCreateSerializer
from events_api.permissions import IsOrganizer


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    permission_classes = [IsOrganizer]

    def get_queryset(self):
        event_id = self.kwargs.get('event_pk')
        return EventSession.objects.filter(event_id=event_id)

    def get_serializer_class(self):
        if self.action == 'create':
            return SessionCreateSerializer
        return SessionSerializer

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_pk')
        serializer.save(event_id=event_id)
