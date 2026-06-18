from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, DateTimeWidget
from .models import Smestaj, SmestajReservation


class SmestajResource(resources.ModelResource):
    company = fields.Field(
        column_name='company',
        attribute='company',
        widget=ForeignKeyWidget('users.CompanyProfile', 'company_name')
    )
    
    class Meta:
        model = Smestaj
        fields = (
            'id', 'company', 'naziv', 'slug', 'opis', 'tip', 'season',
            'cena_po_nocenju', 'udaljenost_od_staza', 'kapacitet',
            'ima_spa', 'ima_bazen', 'ski_in_ski_out', 'ima_restoran',
            'ima_parking', 'ima_wifi', 'is_active'
        )
        import_id_fields = ('id',)


class SmestajAdmin(ImportExportModelAdmin):
    resource_class = SmestajResource
    list_display = ('naziv', 'company', 'tip', 'cena_po_nocenju', 'kapacitet', 'is_active')
    list_filter = ('tip', 'season', 'is_active', 'ima_spa', 'ima_bazen', 'ski_in_ski_out')
    search_fields = ('naziv', 'opis', 'company__company_name')


class SmestajReservationResource(resources.ModelResource):
    smestaj = fields.Field(
        column_name='smestaj',
        attribute='smestaj',
        widget=ForeignKeyWidget(Smestaj, 'naziv')
    )
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget('users.User', 'email')
    )
    
    class Meta:
        model = SmestajReservation
        fields = ('id', 'smestaj', 'user', 'check_in', 'check_out', 
                 'broj_odraslih', 'broj_dece', 'status', 'napomena', 'created_at')
        import_id_fields = ('id',)


class SmestajReservationAdmin(ImportExportModelAdmin):
    resource_class = SmestajReservationResource
    list_display = ('smestaj', 'user', 'check_in', 'check_out', 'status')
    list_filter = ('status', 'check_in', 'check_out')
    search_fields = ('user__email', 'smestaj__naziv')


admin.site.register(Smestaj, SmestajAdmin)
admin.site.register(SmestajReservation, SmestajReservationAdmin)