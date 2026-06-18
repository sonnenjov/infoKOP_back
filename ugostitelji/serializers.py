from rest_framework import serializers
from .models import MenuItem, MenuCategory


class MenuCategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = MenuCategory
    fields = ['id', 'name']
    
    
class MenuItemSerializer(serializers.ModelSerializer):
  category_name = serializers.CharField(source='category.name', read_only=True)
  
  class Meta:
    model = MenuItem
    fields = [
    'id', 'name', 'description', 'price',
    'category', 'category_name',
    'is_available', 'allergens',
    'created_at', 'updated_at',
    ]
    read_only_fields = ['id', 'created_at', 'updated_at', 'category_name']