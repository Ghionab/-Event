from rest_framework import serializers
from advanced.models import Vendor, Contract


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'category', 'contact_name', 'email',
                  'phone', 'website', 'address', 'description',
                  'hourly_rate', 'flat_rate', 'rating', 'review_count',
                  'is_preferred', 'is_blacklisted', 'created_at', 'updated_at']


class ContractSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta:
        model = Contract
        fields = ['id', 'vendor', 'vendor_name', 'title', 'description',
                  'amount', 'payment_terms', 'status',
                  'start_date', 'end_date',
                  'contract_file', 'signed_file',
                  'signed_by_vendor', 'signed_by_client',
                  'vendor_signature_date', 'client_signature_date',
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContractCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['vendor', 'title', 'description', 'amount', 'payment_terms',
                  'start_date', 'end_date', 'status']

    def create(self, validated_data):
        event_id = self.context.get('event_id')
        validated_data['event_id'] = event_id
        return super().create(validated_data)
