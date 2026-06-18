from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('dashboard/', views.admin_dashboard_stats, name='dashboard_stats'),
    
    path('companies/pending/', views.admin_pending_companies, name='pending_companies'),
    path('companies/all/', views.admin_all_companies, name='all_companies'),
    path('companies/<int:company_id>/approve/', views.admin_approve_company, name='approve_company'),
    path('companies/<int:company_id>/reject/', views.admin_reject_company, name='reject_company'),
    
    path('logs/', views.admin_system_logs, name='system_logs'),
    path('logs/create/', views.admin_create_log, name='create_log'),
    
    # path('analytics/users/', views.admin_user_analytics, name='user_analytics'),
    path('activities/', views.admin_activities, name='admin_activities'),
]