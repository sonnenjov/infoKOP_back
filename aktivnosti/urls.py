from django.urls import path
from .views import (
    get_activities,
    get_activity_detail,
    get_my_activities,
    get_my_reservations,
    get_company_reservations,
    create_activity,
    create_reservation,
    update_activity,
    cancel_reservation,
    update_reservation_status,
    delete_activity,
)

app_name = 'activities'

urlpatterns = [
    path('', get_activities, name='get-activities'),
    path('mine/', get_my_activities, name='my-activities'),
    path('create/', create_activity, name='create-activity'),
    path('<slug:slug>/', get_activity_detail, name='activity-detail'),
    path('<int:pk>/update/', update_activity, name='update-activity'),
    path('<int:pk>/delete/', delete_activity, name='delete-activity'),

    path('reservations/mine/', get_my_reservations, name='my-reservations'),
    path('reservations/company/', get_company_reservations, name='company-reservations'),
    path('reservations/create/', create_reservation, name='create-reservation'),
    path('reservations/<int:pk>/cancel/', cancel_reservation, name='cancel-reservation'),
    path('reservations/<int:pk>/status/', update_reservation_status, name='update-reservation-status'),
]