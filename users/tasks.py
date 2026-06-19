from celery import shared_task
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .models import CompanyProfile, User
from .email_utils import (
    send_confirmation_email, send_approval_email, send_admin_approval_request,
    send_rejection_email, send_mail,
    send_user_approval_email, send_user_rejection_email,
    send_user_banned_email, send_user_unbanned_email,
    send_password_reset_email,
)


@shared_task
def send_confirmation_email_task(user_id):
    user = User.objects.get(id=user_id)
    send_confirmation_email(user)


@shared_task
def send_approval_email_task(user_id, company_id):
    user = User.objects.get(id=user_id)
    company = CompanyProfile.objects.get(id=company_id)
    send_approval_email(user, company)


@shared_task
def send_admin_approval_request_task(user_id):
    user = User.objects.get(id=user_id)
    send_admin_approval_request(user)


@shared_task
def send_rejection_email_task(user_id, company_id, reason):
    user = User.objects.get(id=user_id)
    company = CompanyProfile.objects.get(id=company_id)
    send_rejection_email(user, company, reason)


@shared_task
def send_user_approval_email_task(user_id):
    user = User.objects.get(id=user_id)
    send_user_approval_email(user)


@shared_task
def send_user_rejection_email_task(user_id, reason):
    user = User.objects.get(id=user_id)
    send_user_rejection_email(user, reason)


@shared_task
def send_user_banned_email_task(user_id, reason):
    user = User.objects.get(id=user_id)
    send_user_banned_email(user, reason)


@shared_task
def send_user_unbanned_email_task(user_id):
    user = User.objects.get(id=user_id)
    send_user_unbanned_email(user)


@shared_task
def send_password_reset_email_task(user_id, uid, token):
    """
    Send password reset email asynchronously
    Called from request_password_reset view
    """
    try:
        user = User.objects.get(id=user_id)
        send_password_reset_email(user, uid, token)
    except User.DoesNotExist:
        pass