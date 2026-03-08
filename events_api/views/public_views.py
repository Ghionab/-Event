"""
Public API views for participant portal - no authentication required
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from events.models import Event
from events_api.serializers.event_serializers import EventListSerializer, EventSerializer
from events_api.serializers import TicketTypeSerializer, PromoCodeSerializer


class PublicEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API for participants to browse events - no auth required
    """
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'status', 'is_public']
    search_fields = ['title', 'description', 'city', 'country']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        return Event.objects.filter(is_public=True, status='published')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventSerializer
        return EventListSerializer

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get full event details including tracks, rooms, sponsors"""
        event = self.get_object()
        serializer = EventSerializer(event)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tickets(self, request, pk=None):
        """Get available ticket types for event"""
        from registration.models import TicketType
        event = self.get_object()
        tickets = TicketType.objects.filter(event_id=event.id, is_active=True)
        serializer = TicketTypeSerializer(tickets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def validate_promo(self, request, pk=None):
        """Validate a promo code for an event"""
        from registration.models import PromoCode
        code = request.data.get('code', '').upper()
        try:
            promo = PromoCode.objects.get(
                code=code,
                event_id=pk,
                is_active=True
            )
            if promo.is_valid():
                serializer = PromoCodeSerializer(promo)
                return Response({
                    'valid': True,
                    'discount_type': promo.discount_type,
                    'discount_value': float(promo.discount_value)
                })
            return Response({'valid': False, 'error': 'Promo code is expired or max uses reached'})
        except PromoCode.DoesNotExist:
            return Response({'valid': False, 'error': 'Invalid promo code'})
