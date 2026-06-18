
from django.urls import path
from .views import (
    get_dogadjaji,
    get_dogadjaj_detail,
    get_my_dogadjaji,
    create_dogadjaj,
    update_dogadjaj,
    delete_dogadjaj,
    
    create_dogadjaj_reservation,
    get_my_dogadjaj_reservations,
    cancel_dogadjaj_reservation,
    
    get_company_dogadjaj_reservations,
    update_dogadjaj_reservation_status,
    
    get_company_dogadjaj_dashboard_stats,
)

app_name = 'dogadjaji'

urlpatterns = [
    path('', get_dogadjaji, name='dogadjaj-list'),
    path('<slug:slug>/', get_dogadjaj_detail, name='dogadjaj-detail'),
    path('my/', get_my_dogadjaji, name='my-dogadjaji'),
    path('create/', create_dogadjaj, name='create-dogadjaj'),
    path('<int:pk>/update/', update_dogadjaj, name='update-dogadjaj'),
    path('<int:pk>/delete/', delete_dogadjaj, name='delete-dogadjaj'),
    
    path('reservations/', get_my_dogadjaj_reservations, name='my-reservations'),
    path('reservations/create/', create_dogadjaj_reservation, name='create-reservation'),
    path('reservations/<int:pk>/cancel/', cancel_dogadjaj_reservation, name='cancel-reservation'),
    
    path('reservations/company/', get_company_dogadjaj_reservations, name='company-reservations'),
    path('reservations/<int:pk>/status/', update_dogadjaj_reservation_status, name='update-reservation-status'),
    
    path('dashboard/stats/', get_company_dogadjaj_dashboard_stats, name='dashboard-stats'),
]