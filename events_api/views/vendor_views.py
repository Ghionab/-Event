from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from advanced.models import Vendor, Contract
from events_api.serializers import VendorSerializer, ContractSerializer, ContractCreateSerializer
from events_api.permissions import IsOrganizer


class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [IsOrganizer]
    queryset = Vendor.objects.all()

    @action(detail=True, methods=['get'])
    def contracts(self, request, pk=None):
        vendor = self.get_object()
        contracts = vendor.contract_set.all()
        serializer = ContractSerializer(contracts, many=True)
        return Response(serializer.data)


class ContractViewSet(viewsets.ModelViewSet):
    serializer_class = ContractSerializer
    permission_classes = [IsOrganizer]

    def get_queryset(self):
        event_id = self.kwargs.get('event_pk')
        return Contract.objects.filter(event_id=event_id)

    def get_serializer_class(self):
        if self.action == 'create':
            return ContractCreateSerializer
        return ContractSerializer

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_pk')
        serializer.save(event_id=event_id)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None, event_pk=None):
        contract = self.get_object()
        contract.status = 'active'
        contract.save()
        return Response({'message': 'Contract activated'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None, event_pk=None):
        contract = self.get_object()
        contract.status = 'completed'
        contract.save()
        return Response({'message': 'Contract completed'})
