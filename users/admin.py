from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, DateTimeWidget
from .models import User, CompanyProfile, ServiceCategory, Service, CompanyOfferedService, ActivityLog


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'role', 'phone', 'email_confirmed', 'is_approved', 'is_active', 'is_staff', 'is_superuser')
        export_order = ('id', 'email', 'username', 'role', 'phone', 'email_confirmed', 'is_approved', 'is_active')


class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    resource_class = UserResource
    list_display = ('email', 'username', 'role', 'email_confirmed', 'is_approved', 'is_active')
    list_filter = ('role', 'email_confirmed', 'is_approved', 'is_active')
    search_fields = ('email', 'username')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone', 'avatar', 'email_confirmed', 'is_approved')}),
    )


class CompanyProfileResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'email')
    )
    
    class Meta:
        model = CompanyProfile
        fields = ('id', 'user', 'type', 'company_name', 'address', 'pib', 'slug', 'cover_photo', 'logo')
        export_order = ('id', 'user', 'company_name', 'type', 'address', 'pib', 'slug')
        import_id_fields = ('id',)


class CompanyProfileAdmin(ImportExportModelAdmin):
    resource_class = CompanyProfileResource
    list_display = ('company_name', 'user', 'type', 'pib', 'slug', 'total_revenue', 'total_reservations')
    list_filter = ('type',)
    search_fields = ('company_name', 'address', 'pib', 'user__email')
    raw_id_fields = ('user',)
    readonly_fields = ('total_revenue', 'total_reservations', 'total_guests', 'monthly_revenue', 'yearly_revenue')


class ServiceCategoryResource(resources.ModelResource):
    class Meta:
        model = ServiceCategory
        fields = ('id', 'name', 'icon')


class ServiceCategoryAdmin(ImportExportModelAdmin):
    resource_class = ServiceCategoryResource
    list_display = ('name', 'icon')
    search_fields = ('name',)


class ServiceResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(ServiceCategory, 'name')
    )
    
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'category', 'base_price', 'duration_minutes', 'is_active')
        import_id_fields = ('id',)


class ServiceAdmin(ImportExportModelAdmin):
    resource_class = ServiceResource
    list_display = ('name', 'category', 'base_price', 'duration_minutes', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')


class CompanyOfferedServiceResource(resources.ModelResource):
    company = fields.Field(
        column_name='company',
        attribute='company',
        widget=ForeignKeyWidget(CompanyProfile, 'company_name')
    )
    service = fields.Field(
        column_name='service',
        attribute='service',
        widget=ForeignKeyWidget(Service, 'name')
    )
    
    class Meta:
        model = CompanyOfferedService
        fields = ('id', 'company', 'service', 'custom_price', 'is_available', 'max_capacity', 'requires_advance_booking_days')
        import_id_fields = ('id',)


class CompanyOfferedServiceAdmin(ImportExportModelAdmin):
    resource_class = CompanyOfferedServiceResource
    list_display = ('company', 'service', 'effective_price', 'is_available', 'max_capacity')
    list_filter = ('is_available',)
    search_fields = ('company__company_name', 'service__name')
    raw_id_fields = ('company', 'service')


class ActivityLogResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'email')
    )
    
    created_at = fields.Field(
        column_name='created_at',
        attribute='created_at',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )
    
    class Meta:
        model = ActivityLog
        fields = ('id', 'user', 'action', 'description', 'created_at')
        export_order = ('id', 'user', 'action', 'description', 'created_at')


class ActivityLogAdmin(ImportExportModelAdmin):
    resource_class = ActivityLogResource
    list_display = ('user', 'action', 'description', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'description')


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(CompanyProfile)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)
admin.site.register(CompanyProfile, CompanyProfileAdmin)
admin.site.register(ServiceCategory, ServiceCategoryAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(CompanyOfferedService, CompanyOfferedServiceAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)