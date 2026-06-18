from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.db import transaction
import logging
import traceback
import psutil,time

from .models import SystemLog
from users.models import User, CompanyProfile
from users.permissions import IsAdmin

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_dashboard_stats(request):
    try:
        print("=" * 50)
        print("Dashboard request received")
        print(f"User: {request.user.email}")
        print(f"Role: {request.user.role}")
        print("=" * 50)

        SystemLog.objects.create(
            type='info',
            message='Admin dashboard accessed',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        now = timezone.now()
        traffic = []
        for i in range(24):
          hour_start = now - timedelta(hours=i+1)
          hour_end = now - timedelta(hours=i)
          count = CompanyProfile.objects.filter(
              user__date_joined__gte=hour_start,
              user__date_joined__lt=hour_end
          ).count()
          traffic.append({
              'label': hour_start.strftime('%H:00'),
              'count': count,
              'value': min(count * 20, 100)
          })
        
        
        
        total_partners = CompanyProfile.objects.count()
        active_listings = CompanyProfile.objects.filter(
            user__is_approved=True,
            user__is_active=True
        ).count()

        yesterday = timezone.now() - timedelta(days=1)
        daily_active_users = User.objects.filter(
            last_login__gte=yesterday,
            is_active=True
        ).count()

        pending_approvals = CompanyProfile.objects.filter(
            user__is_approved=False,
            user__role=User.Role.COMPANY
        ).count()

        recent_companies = CompanyProfile.objects.filter(
            user__role=User.Role.COMPANY
        ).select_related('user').order_by('-user__date_joined')[:5]
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

        recent_logs_qs = SystemLog.objects.select_related('user').order_by('-timestamp')[:10]
        logs_data = []
        for log in recent_logs_qs:
            logs_data.append({
                'id': log.id,
                'type': log.type,
                'message': log.message,
                'timestamp': log.timestamp,
                'user': f"{log.user.first_name} {log.user.last_name}".strip() if log.user else 'System',
                'ip_address': log.ip_address
            })

        response_data = {
            'total_partners': total_partners,
            'active_listings': active_listings,
            'daily_active_users': daily_active_users,
            'server_uptime': int(uptime_seconds),
            'pending_approvals': pending_approvals,
            'recent_logs': logs_data,
            'booking_traffic': list(reversed(traffic)),
            'system_load': {
                'api': round(cpu, 1),
                'database': round(memory, 1),
                'cdn': round(disk, 1)
            },
            'recent_companies': []
        }

        for company in recent_companies:
            response_data['recent_companies'].append({
                'id': company.id,
                'company_name': company.company_name,
                'email': company.user.email,
                'type': company.type,
                'created_at': company.user.date_joined,
                'is_approved': company.user.is_approved
            })

        return Response(response_data)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {'error': str(e), 'detail': 'Check server logs for more information'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_pending_companies(request):
    try:
        companies = CompanyProfile.objects.filter(
            user__is_approved=False,
            user__role=User.Role.COMPANY
        ).select_related('user')

        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        paginator = Paginator(companies, page_size)
        page_obj = paginator.get_page(page)

        results = []
        for company in page_obj:
            results.append({
                'id': company.id,
                'company_name': company.company_name,
                'email': company.user.email,
                'phone': company.user.phone,
                'type': company.type,
                'address': company.address,
                'pib': company.pib,
                'created_at': company.user.date_joined,
                'user': {
                    'id': company.user.id,
                    'email': company.user.email,
                    'first_name': company.user.first_name,
                    'last_name': company.user.last_name,
                }
            })

        return Response({
            'results': results,
            'total': paginator.count,
            'page': int(page),
            'total_pages': paginator.num_pages
        })

    except Exception as e:
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_approve_company(request, company_id):
    try:
        with transaction.atomic():
            company = CompanyProfile.objects.get(id=company_id)

            if company.user.is_approved:
                return Response(
                    {'error': 'Company is already approved'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = company.user
            user.is_approved = True
            user.is_active = True
            user.save()

            SystemLog.objects.create(
                type='admin',
                message=f'Company "{company.company_name}" approved',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({
            'success': True,
            'message': f'Company {company.company_name} approved successfully'
        })

    except CompanyProfile.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_reject_company(request, company_id):
    try:
        reason = request.data.get('reason', 'No reason provided')

        with transaction.atomic():
            company = CompanyProfile.objects.get(id=company_id)

            if company.user.is_approved:
                return Response(
                    {'error': 'Company is already approved'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = company.user
            user.is_active = False
            user.is_approved = False
            user.save()

            SystemLog.objects.create(
                type='admin',
                message=f'Company "{company.company_name}" rejected. Reason: {reason}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({
            'success': True,
            'message': f'Company {company.company_name} rejected'
        })

    except CompanyProfile.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_all_companies(request):
    try:
        status_filter = request.query_params.get('status', 'all')
        type_filter = request.query_params.get('type', 'all')

        companies = CompanyProfile.objects.select_related('user')

        if status_filter == 'approved':
            companies = companies.filter(user__is_approved=True)
        elif status_filter == 'pending':
            companies = companies.filter(user__is_approved=False)
        elif status_filter == 'rejected':
            companies = companies.filter(user__is_active=False, user__is_approved=False)

        if type_filter != 'all':
            companies = companies.filter(type=type_filter)

        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        paginator = Paginator(companies, page_size)
        page_obj = paginator.get_page(page)

        results = []
        for company in page_obj:
            results.append({
                'id': company.id,
                'company_name': company.company_name,
                'email': company.user.email,
                'phone': company.user.phone,
                'type': company.type,
                'address': company.address,
                'pib': company.pib,
                'is_approved': company.user.is_approved,
                'is_active': company.user.is_active,
                'created_at': company.user.date_joined,
                'user': {
                    'id': company.user.id,
                    'email': company.user.email,
                    'first_name': company.user.first_name,
                    'last_name': company.user.last_name,
                }
            })

        return Response({
            'results': results,
            'total': paginator.count,
            'page': int(page),
            'total_pages': paginator.num_pages
        })

    except Exception as e:
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_system_logs(request):
    try:
        log_type = request.query_params.get('type', 'all')
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        logs = SystemLog.objects.select_related('user').order_by('-timestamp')

        if log_type != 'all':
            logs = logs.filter(type=log_type)

        paginator = Paginator(logs, page_size)
        page_obj = paginator.get_page(page)

        results = []
        for log in page_obj:
            results.append({
                'id': log.id,
                'type': log.type,
                'message': log.message,
                'timestamp': log.timestamp,
                'user': f"{log.user.first_name} {log.user.last_name}".strip() if log.user else 'System',
                'ip_address': log.ip_address
            })

        return Response({
            'results': results,
            'total': paginator.count,
            'page': int(page),
            'total_pages': paginator.num_pages
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_create_log(request):
    try:
        message = request.data.get('message')
        log_type = request.data.get('type', 'info')

        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        SystemLog.objects.create(
            type=log_type,
            message=message,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({'success': True, 'message': 'Log created successfully'})

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_user_analytics(request):
    try:
        user_counts = User.objects.values('role').annotate(count=Count('id'))

        week_ago = timezone.now() - timedelta(days=7)
        new_users = User.objects.filter(date_joined__gte=week_ago).count()

        daily_growth = []
        for i in range(7, -1, -1):
            day = timezone.now() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            count = User.objects.filter(
                date_joined__gte=day_start,
                date_joined__lte=day_end
            ).count()
            daily_growth.append({'date': day.strftime('%Y-%m-%d'), 'count': count})

        return Response({
            'user_counts_by_role': user_counts,
            'new_users_last_7_days': new_users,
            'daily_growth': daily_growth,
            'total_users': User.objects.count()
        })

    except Exception as e:
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_activities(request):
    try:
        return Response([])
    except Exception as e:
        return Response({'error': str(e)}, status=500)