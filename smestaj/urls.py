
from django.urls import path
from .views import (
    get_smestaji,
    get_smestaj_detail,
    
    get_my_smestaji,
    create_smestaj,
    update_smestaj,
    delete_smestaj,
    
    create_smestaj_reservation,
    get_my_smestaj_reservations,
    cancel_smestaj_reservation,
    
    get_company_smestaj_reservations,
    update_smestaj_reservation_status,
    
    get_company_dashboard_stats,
)

app_name = 'smestaj'

urlpatterns = [
    path('', get_smestaji, name='smestaj-list'),
    path('<slug:slug>/', get_smestaj_detail, name='smestaj-detail'),
    
    path('my/', get_my_smestaji, name='my-smestaji'),
    path('create/', create_smestaj, name='create-smestaj'),
    path('<int:pk>/update/', update_smestaj, name='update-smestaj'),
    path('<int:pk>/delete/', delete_smestaj, name='delete-smestaj'),
    
    path('reservations/', get_my_smestaj_reservations, name='my-reservations'),
    path('reservations/create/', create_smestaj_reservation, name='create-reservation'),
    path('reservations/<int:pk>/cancel/', cancel_smestaj_reservation, name='cancel-reservation'),
    
    path('reservations/company/', get_company_smestaj_reservations, name='company-reservations'),
    path('reservations/<int:pk>/status/', update_smestaj_reservation_status, name='update-reservation-status'),
    
    path('dashboard/stats/', get_company_dashboard_stats, name='dashboard-stats'),
]