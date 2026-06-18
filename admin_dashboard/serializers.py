from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import CompanyProfile, User
from users.serializers import UserListSerializer
from .models import SystemLog, AdminActivity

User = get_user_model()

class SystemLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemLog
        fields = ['id', 'type', 'message', 'user_name', 'timestamp']
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        return None

class AdminCompanyDetailSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    is_approved = serializers.BooleanField(source='user.is_approved', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    service_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'user', 'email', 'phone', 'company_name', 'type', 
            'address', 'pib', 'slug', 'service_count', 'is_approved',
            'created_at'
        ]
    
    def get_service_count(self, obj):
        try:
            return obj.offered_services.count() if hasattr(obj, 'offered_services') else 0
        except:
            return 0