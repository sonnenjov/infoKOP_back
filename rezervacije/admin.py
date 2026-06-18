from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display  = ['id', 'guest', 'company', 'service_name', 'date_from', 'status', 'amount']
    list_filter   = ['status', 'company', 'service_type']
    search_fields = ['guest__email', 'company__company_name', 'service_name']
    list_editable = ['status']