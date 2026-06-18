from rest_framework import serializers
from .models import Vest, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class VestSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        source='tags',
        required=False
    )
    image = serializers.SerializerMethodField()
    image_url = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    class Meta:
        model = Vest
        fields = [
            'id', 'theme', 'title', 'image', 'image_url',
            'text', 'created_at', 'author', 'status', 'priority',
            'is_visible', 'tags', 'tag_ids', 'seo_title', 'seo_desc',
            'views_count', 'updated_at', 'published_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'views_count', 'author']

    def get_image(self, obj):
        if obj.image:
            return obj.image.url if hasattr(obj.image, 'url') else obj.image
        return None

    def create(self, validated_data):
        image_url = validated_data.pop('image_url', None)
        instance = super().create(validated_data)
        if image_url:
            instance.image = image_url
            instance.save()
        return instance

    def update(self, instance, validated_data):
        image_url = validated_data.pop('image_url', None)
        instance = super().update(instance, validated_data)
        if image_url:
            instance.image = image_url
            instance.save()
        return instance