from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from events.models import Event
from events_api.serializers.event_serializers import (
    EventSerializer, EventCreateSerializer, EventListSerializer,
    TrackSerializer, RoomSerializer, SponsorSerializer
)
from events_api.permissions import IsOrganizerOrReadOnly, IsEventOrganizer, IsPublicEventOrReadOnly


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'status', 'is_public']
    search_fields = ['title', 'description', 'city', 'country']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPublicEventOrReadOnly]
        else:
            permission_classes = [IsOrganizerOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role in ['organizer', 'admin']:
            return Event.objects.filter(organizer=user)
        return Event.objects.filter(is_public=True)

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        event = self.get_object()
        tracks = event.tracks.all()
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def rooms(self, request, pk=None):
        event = self.get_object()
        rooms = event.rooms.all()
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sponsors(self, request, pk=None):
        event = self.get_object()
        sponsors = event.sponsors.all()
        serializer = SponsorSerializer(sponsors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        event = self.get_object()
        if event.organizer != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to publish this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        event.status = 'published'
        event.is_public = True
        event.save()
        return Response({'message': 'Event published successfully', 'status': event.status})

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        event = self.get_object()
        if event.organizer != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to unpublish this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        event.status = 'draft'
        event.save()
        return Response({'message': 'Event unpublished', 'status': event.status})


class TrackViewSet(viewsets.ModelViewSet):
    serializer_class = None  # Will be set dynamically
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        event_id = self.kwargs.get('event_pk')
        from events.models import Track
        return Track.objects.filter(event_id=event_id)

    def get_serializer_class(self):
        from events_api.serializers import TrackSerializer
        return TrackSerializer

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_pk')
        serializer.save(event_id=event_id)


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = None  # Will be set dynamically
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        event_id = self.kwargs.get('event_pk')
        from events.models import Room
        return Room.objects.filter(event_id=event_id)

    def get_serializer_class(self):
        from events_api.serializers import RoomSerializer
        return RoomSerializer

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_pk')
        serializer.save(event_id=event_id)


class SponsorViewSet(viewsets.ModelViewSet):
    serializer_class = None  # Will be set dynamically
    permission_classes = [IsOrganizerOrReadOnly]

    def get_queryset(self):
        event_id = self.kwargs.get('event_pk')
        from events.models import Sponsor
        return Sponsor.objects.filter(event_id=event_id)

    def get_serializer_class(self):
        from events_api.serializers import SponsorSerializer
        return SponsorSerializer

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_pk')
        serializer.save(event_id=event_id)
