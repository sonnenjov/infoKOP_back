# users/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.pagination import PageNumberPagination
from .models import User, CompanyProfile, ActivityLog
from django.contrib.auth.password_validation import validate_password
from django.db import transaction


# Add your existing pagination classes
class PageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# Add your existing token serializer
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        return data


# Activity Log Serializer
class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ['id', 'action', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'phone', 'role', 'avatar']  # Add 'avatar' here
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone': {'required': False},
            'avatar': {'required': False},  
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role=validated_data.get('role', User.Role.USER)
        )
        return user

# Company Register Serializer
class CompanyRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    company_name = serializers.CharField(write_only=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    pib = serializers.CharField(write_only=True, required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=CompanyProfile.PARTNER_TYPE_CHOICES, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'company_name', 'address', 'phone', 'pib', 'type']

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                phone=validated_data.get('phone', ''),
                role=User.Role.COMPANY,
                is_active=False,
                is_approved=False,
            )
            
            CompanyProfile.objects.create(
                user=user,
                company_name=validated_data['company_name'],
                address=validated_data.get('address', ''),
                pib=validated_data.get('pib', ''),
                type=validated_data['type'],
            )
            
            return user


class CompanyProfileSerializer(serializers.ModelSerializer):
    cover_photo = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    class Meta:
        model = CompanyProfile
        fields = ['id', 'company_name', 'address', 'pib', 'type', 'slug', 'cover_photo', 'logo']
        read_only_fields = ['slug']

    def get_cover_photo(self, obj):
        return obj.cover_photo.url if obj.cover_photo else None

    def get_logo(self, obj):
        return obj.logo.url if obj.logo else None


class CompanyProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ['company_name', 'address', 'pib', 'type']


# User List Serializer (for admin)
class UserListSerializer(serializers.ModelSerializer):
    company_profile = CompanyProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'role',
            'phone',
            'avatar',
            'email_confirmed',
            'is_approved',
            'is_active',
            'date_joined',
            'company_profile'
        ]