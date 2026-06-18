from rest_framework import serializers
from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    guest_name  = serializers.CharField(source='guest.get_full_name', read_only=True)
    guest_email = serializers.EmailField(source='guest.email', read_only=True)
    company_name = serializers.CharField(source='company.company_name', read_only=True)

    class Meta:
        model  = Reservation
        fields = [
            'id', 'guest', 'guest_name', 'guest_email',
            'company', 'company_name',
            'service_name', 'service_type',
            'date_from', 'date_to', 'guests', 'notes',
            'status', 'amount', 'source',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'guest', 'company', 'created_at', 'updated_at',
                            'guest_name', 'guest_email', 'company_name']


class ReservationCreateSerializer(serializers.ModelSerializer):
    company = serializers.IntegerField(write_only=True)

    class Meta:
        model = Reservation
        fields = [
            'company', 'service_name', 'service_type',
            'date_from', 'date_to', 'guests', 'notes', 'amount',
            'source', 'channel', 'status',
        ]
        extra_kwargs = {
            'date_to': {'required': False, 'allow_null': True},
            'notes':   {'required': False, 'allow_blank': True},
            'amount':  {'required': False},
            'source':  {'required': False},
            'channel': {'required': False},
            'status':  {'required': False},
        }

    def validate_company(self, value):
        from users.models import CompanyProfile
        try:
            return CompanyProfile.objects.get(id=value)
        except CompanyProfile.DoesNotExist:
            try:
                return CompanyProfile.objects.get(user_id=value)
            except CompanyProfile.DoesNotExist:
                raise serializers.ValidationError(
                    f"No company profile found for id or user_id {value}."
                )
class ReservationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Reservation
        fields = ['status']