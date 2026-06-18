from django.urls import path 
from . import views
from .views import (
    Register_User_View,
    company_profile_management,
    create_company_profile,
    delete_company_image,
    get_my_activity,
    get_users,
    get_my_profile,
    get_my_company_profile,
    get_companies,
    update_my_profile,
    verify_email,
    two_factor_login_verify,
    change_password
)
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MyTokenObtainPairView 

app_name = 'users'

urlpatterns = [
    path('register/', Register_User_View.as_view(), name='register'),
    path('register/company/', create_company_profile, name='register-company'),
    path('all/users/', get_users, name='get-users'),        
    path('all/companies/', get_companies, name='get-companies'),        
    path('me/', get_my_profile, name='my-profile'),         
    path('me/update/', update_my_profile, name='update_my-profile'),         
    path('me/company/', get_my_company_profile, name='my-company'),  
    path('token/', MyTokenObtainPairView.as_view(), name='token'),        
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('verify-email/', verify_email, name='verify-email'),
    path("me/change-password/", change_password , name="change_password"),
    path('password-reset/', views.request_password_reset, name='password_reset'),
    path('password-reset/confirm/', views.confirm_password_reset, name='password_reset_confirm'),
    path('companies/public/', views.get_public_companies, name='public_companies'),
    path('me/activity_user/', get_my_activity, name="get user activity"),
    path('2fa/login/verify/', views.two_factor_login_verify, name='2fa_login_verify'),
    path('2fa/status/', views.two_factor_status, name='2fa_status'),
    path('2fa/enable/', views.two_factor_enable, name='2fa_enable'),
    path('2fa/verify/', views.two_factor_verify, name='2fa_verify'),
    path('2fa/disable/', views.two_factor_disable, name='2fa_disable'),
    path('company/my-profile/', get_my_company_profile, name='my-company-profile'),
    path('company/update/', company_profile_management, name='company-update'),
    path('company/profile/', company_profile_management, name='company-profile'),
    path('company/delete-image/<str:image_type>/', delete_company_image, name='delete-company-image'),
    path('all/companies/', views.get_companies, name='get-companies'),
    path('admin/users/<int:user_id>/approve/', views.admin_approve_user, name='admin-approve-user'),
    path('admin/users/<int:user_id>/reject/', views.admin_reject_user, name='admin-reject-user'),
    path('admin/users/<int:user_id>/ban/', views.admin_ban_user, name='admin-ban-user'),
    path('admin/users/<int:user_id>/unban/', views.admin_unban_user, name='admin-unban-user'),
    path('admin/companies/<int:company_id>/approve/', views.admin_approve_company, name='admin-approve-company'),
    path('admin/companies/<int:company_id>/reject/', views.admin_reject_company, name='admin-reject-company'),
]