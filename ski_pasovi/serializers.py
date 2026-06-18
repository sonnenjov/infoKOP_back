from rest_framework import serializers
from .models import SkiPass
from .utils.qr_utils import generate_qr_base64

class SkiPassSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()
    qr_code = serializers.SerializerMethodField()

    class Meta:
        model = SkiPass
        fields = [
            'id', 'code', 'pass_type',
            'purchased_at', 'valid_from', 'valid_until',
            'is_used', 'used_at', 'price_paid',
            'is_valid', 'qr_code',
        ]
        read_only_fields = fields  
    def get_is_valid(self, obj):
        return obj.is_valid()

    def get_qr_code(self, obj):
        from ski_pasovi.utils.qr_utils import generate_qr_base64
        return f'data:image/png;base64,{generate_qr_base64(obj.code)}'


class SkiPassScanSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = SkiPass
        fields = [
            'code', 'pass_type',
            'valid_from', 'valid_until',
            'is_used', 'used_at',
            'is_valid', 'user_email',
        ]

    def get_is_valid(self, obj):
        return obj.is_valid()