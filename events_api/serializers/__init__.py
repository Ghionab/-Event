from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone', 'company', 'job_title']
        read_only_fields = ['id', 'role']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


# Import all serializers from modules
from .event_serializers import (
    EventSerializer,
    EventCreateSerializer,
    EventListSerializer,
    TrackSerializer,
    RoomSerializer,
    SponsorSerializer,
)

from .speaker_serializers import (
    SpeakerSerializer,
    SpeakerCreateSerializer,
)

from .session_serializers import (
    SessionSerializer,
    SessionCreateSerializer,
)

from .vendor_serializers import (
    VendorSerializer,
    ContractSerializer,
    ContractCreateSerializer,
)

from .registration_serializers import (
    TicketTypeSerializer,
    PromoCodeSerializer,
    RegistrationSerializer,
    RegistrationCreateSerializer,
)
