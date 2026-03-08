from rest_framework import serializers
from registration.models import Registration, TicketType, PromoCode


class TicketTypeSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()
    is_sold_out = serializers.SerializerMethodField()
    ticket_category = serializers.SerializerMethodField()

    class Meta:
        model = TicketType
        fields = ['id', 'name', 'description', 'price', 'quantity_available',
                  'quantity_sold', 'available', 'is_sold_out', 'ticket_category',
                  'sales_start', 'sales_end', 'is_active', 'benefits']

    def get_available(self, obj):
        return obj.available_quantity

    def get_is_sold_out(self, obj):
        return obj.is_sold_out

    def get_ticket_category(self, obj):
        return obj.get_ticket_category_display()


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ['id', 'code', 'discount_type', 'discount_value',
                  'max_uses', 'current_uses', 'is_active', 'valid_from', 'valid_until']


class PromoCodeValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


class RegistrationSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    is_checked_in = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        fields = ['id', 'registration_number', 'event', 'event_title',
                  'ticket_type', 'ticket_type_name',
                  'attendee_name', 'attendee_email', 'attendee_phone',
                  'status', 'qr_code', 'is_checked_in', 'checked_in_at', 'checked_in_by',
                  'special_requests', 'custom_fields',
                  'total_amount', 'discount_amount', 'promo_code',
                  'refund_amount', 'refunded_at',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'registration_number', 'qr_code', 'created_at', 'updated_at']

    def get_is_checked_in(self, obj):
        return obj.status == 'checked_in' or obj.checked_in_at is not None


class RegistrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ['ticket_type', 'attendee_name', 'attendee_email',
                  'attendee_phone', 'special_requests', 'promo_code']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
