from django.urls import path 
from rest_framework.routers import DefaultRouter
from . import views
from django.conf.urls.static import static


urlpatterns = [
    path('fetchweather/', views.get_external_data, name="fetch"),
]
