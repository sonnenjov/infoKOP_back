from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, DateTimeWidget
from .models import Dogadjaj, DogadjajReservation


class DogadjajResource(resources.ModelResource):
    company = fields.Field(
        column_name='company',
        attribute='company',
        widget=ForeignKeyWidget('users.CompanyProfile', 'company_name')
    )
    
    class Meta:
        model = Dogadjaj
        fields = (
            'id', 'company', 'naziv', 'slug', 'opis', 'kategorija', 'season',
            'datum_pocetka', 'datum_zavrsetka', 'vreme', 'lokacija',
            'cena', 'max_kapacitet', 'is_active'
        )
        import_id_fields = ('id',)


class DogadjajAdmin(ImportExportModelAdmin):
    resource_class = DogadjajResource
    list_display = ('naziv', 'company', 'kategorija', 'datum_pocetka', 'cena', 'is_active')
    list_filter = ('kategorija', 'season', 'is_active')
    search_fields = ('naziv', 'opis', 'company__company_name')


class DogadjajReservationResource(resources.ModelResource):
    dogadjaj = fields.Field(
        column_name='dogadjaj',
        attribute='dogadjaj',
        widget=ForeignKeyWidget(Dogadjaj, 'naziv')
    )
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget('users.User', 'email')
    )
    
    class Meta:
        model = DogadjajReservation
        fields = ('id', 'dogadjaj', 'user', 'broj_karata', 'status', 'napomena', 'created_at')
        import_id_fields = ('id',)


class DogadjajReservationAdmin(ImportExportModelAdmin):
    resource_class = DogadjajReservationResource
    list_display = ('dogadjaj', 'user', 'broj_karata', 'status')
    list_filter = ('status',)
    search_fields = ('user__email', 'dogadjaj__naziv')


admin.site.register(Dogadjaj, DogadjajAdmin)
admin.site.register(DogadjajReservation, DogadjajReservationAdmin)