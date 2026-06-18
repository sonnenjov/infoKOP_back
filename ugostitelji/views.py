from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MenuCategory, MenuItem
from .serializers import MenuItemSerializer, MenuCategorySerializer


class IsCompanyOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.company.user == request.user


class MenuCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.AllowAny]


class MenuItemViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwner]

    def get_queryset(self):
        return MenuItem.objects.filter(
            company=self.request.user.company_profile
        ).select_related('category')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company_profile)

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        item = self.get_object()
        item.is_available = not item.is_available
        item.save()
        return Response({'id': item.id, 'is_available': item.is_available})