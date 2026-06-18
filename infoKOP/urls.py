"""
URL configuration for infoKOP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from django.urls import path,include
from two_factor.urls import urlpatterns as tf_urls
from two_factor.admin import AdminSiteOTPRequired
admin.site.__class__ = AdminSiteOTPRequired
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/weather/', include('weather.urls')),
    path('api/admin/', include('admin_dashboard.urls')),  
    path('api/aktivnosti/', include('aktivnosti.urls')),
    path('api/core/', include('core.urls')),
    path('api/dogadjaji/', include('dogadjaji.urls')),
    path('api/rezervacije/', include('rezervacije.urls')),
    path('api/skipass/', include('ski_pasovi.urls')),
    path('api/smestaj/', include('smestaj.urls')),
    path('api/ugostitelji/', include('ugostitelji.urls')),
    path('api/users/', include('users.urls')),
    path('api/usluge/', include('usluge.urls')),
    path('api/news/', include('vesti.urls')),
    path('', include(tf_urls)),
    path('api/newsletter/', include('newsletter_api.urls')),
    path('api/aktivnosti/', include('aktivnosti.urls')),
]
