from django.urls import path
from . import views

urlpatterns = [
    path('purchase/', views.purchase_skipass, name='purchase_skipass'),
    path('my-passes/', views.my_passes, name='my_passes'),
    path('validate/', views.validate_skipass, name='validate_skipass'),
]