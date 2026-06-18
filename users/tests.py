from django.test import TestCase
from rest_framework import path
from . import views
# Create your tests here.

path('api/company/create/', views.create_company_profile, name='create_company'),