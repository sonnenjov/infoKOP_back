from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination

from .models import Activity, Reservation


class ActivitySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    company_slug = serializers.CharField(source='company.slug', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            'id', 'company', 'company_name', 'company_slug', 'title', 'slug',
            'description', 'season', 'price', 'duration_minutes', 'max_capacity',
            'location', 'image', 'image_url', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class ActivityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            'title', 'description', 'season', 'price', 'duration_minutes',
            'max_capacity', 'location', 'image', 'is_active'
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Cena mora biti veća od 0.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        validated_data['company'] = request.user.company_profile
        return super().create(validated_data)


class ReservationSerializer(serializers.ModelSerializer):
    activity_title = serializers.CharField(source='activity.title', read_only=True)
    company_name = serializers.CharField(source='activity.company.company_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'activity', 'activity_title', 'company_name', 'user', 'user_email',
            'date', 'time', 'number_of_people', 'status', 'note', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'created_at']

    def validate(self, data):
        activity = data.get('activity') or getattr(self.instance, 'activity', None)
        people = data.get('number_of_people', getattr(self.instance, 'number_of_people', 1))

        if activity and people > activity.max_capacity:
            raise serializers.ValidationError({
                'number_of_people': f'Maksimalan broj osoba za ovu aktivnost je {activity.max_capacity}.'
            })
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReservationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['status']


class ActivityPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100