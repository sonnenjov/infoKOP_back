from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes  
from rest_framework.response import Response
from rest_framework import status

from admin_dashboard.models import SystemLog
from users.email_utils import send_password_reset_email
from users.models import ActivityLog, CompanyProfile
from users.tasks import (
    send_admin_approval_request_task, send_approval_email_task,
    send_confirmation_email_task, send_rejection_email_task,
    send_user_approval_email_task, send_user_rejection_email_task,
    send_user_banned_email_task, send_user_unbanned_email_task,
)
from .serializers import ActivityLogSerializer, CompanyRegisterSerializer, User, UserListSerializer, UserRegisterSerializer, CompanyProfileSerializer, CompanyProfileUpdateSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer, PageNumberPagination, UserPagination
from .permissions import IsAdmin, IsCompany, IsUser, isReporter, isReporterOrAdmin
from django.http import JsonResponse
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import json
import pyotp
import qrcode
from io import BytesIO
import base64
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import binascii
from django.core.cache import cache
from django.core import signing
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    ActivityLog.objects.create(user=request.user, action='password', description='Promenjena lozinka')
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    if not current_password or not new_password:
        return Response({"error": "Sva polja su obavezna"}, status=400)

    if not user.check_password(current_password):
        return Response({"error": "Trenutna lozinka nije ispravna"}, status=400)

    if len(new_password) < 8:
        return Response({"error": "Nova lozinka mora imati najmanje 8 karaktera"}, status=400)

    user.set_password(new_password)
    user.save()
    return Response({"success": True, "message": "Lozinka uspešno promenjena"})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_approve_company(request, company_id):
    try:
        with transaction.atomic():
            company = CompanyProfile.objects.get(id=company_id)
            if company.user.is_approved:
                return Response({'error': 'Company is already approved'}, status=400)
            
            user = company.user
            user.is_approved = True
            user.is_active = True
            user.save()

            send_approval_email_task.delay(user.id, company.id)

            SystemLog.objects.create(
                type='admin',
                message=f'Company "{company.company_name}" approved',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({'success': True, 'message': f'Company {company.company_name} approved successfully'})
    except CompanyProfile.DoesNotExist:
        return Response({'error': 'Company not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_reject_company(request, company_id):
    try:
        reason = request.data.get('reason', 'No reason provided')
        with transaction.atomic():
            company = CompanyProfile.objects.get(id=company_id)
            if company.user.is_approved:
                return Response({'error': 'Company is already approved'}, status=400)

            user = company.user
            user.is_active = False
            user.is_approved = False
            user.save()

            transaction.on_commit(
                lambda: send_rejection_email_task.delay(user.id, company.id, reason)
            )

            SystemLog.objects.create(
                type='admin',
                message=f'Company "{company.company_name}" rejected. Reason: {reason}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({'success': True, 'message': f'Company {company.company_name} rejected'})
    except CompanyProfile.DoesNotExist:
        return Response({'error': 'Company not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_approve_user(request, user_id):
    try:
        with transaction.atomic():
            user = User.objects.get(id=user_id, role=User.Role.USER)
            if user.is_approved:
                return Response({'error': 'User is already approved'}, status=400)

            user.is_approved = True
            user.is_active = True
            user.save()

            send_user_approval_email_task.delay(user.id)

            SystemLog.objects.create(
                type='admin',
                message=f'User "{user.email}" approved',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({'success': True, 'message': f'User {user.email} approved successfully'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_reject_user(request, user_id):
    try:
        reason = request.data.get('reason', 'No reason provided')
        with transaction.atomic():
            user = User.objects.get(id=user_id, role=User.Role.USER)
            if user.is_approved:
                return Response({'error': 'User is already approved'}, status=400)

            user.is_active = False
            user.is_approved = False
            user.save()

            transaction.on_commit(
                lambda: send_user_rejection_email_task.delay(user.id, reason)
            )

            SystemLog.objects.create(
                type='admin',
                message=f'User "{user.email}" rejected. Reason: {reason}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({'success': True, 'message': f'User {user.email} rejected'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_ban_user(request, user_id):
    try:
        reason = request.data.get('reason', 'No reason provided')
        with transaction.atomic():
            user = User.objects.get(id=user_id, role=User.Role.USER)
            if not user.is_active:
                return Response({'error': 'User is already banned'}, status=400)

            user.is_active = False
            user.save()

            transaction.on_commit(
                lambda: send_user_banned_email_task.delay(user.id, reason)
            )

            SystemLog.objects.create(
                type='admin',
                message=f'User "{user.email}" banned. Reason: {reason}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({'success': True, 'message': f'User {user.email} banned'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_unban_user(request, user_id):
    try:
        with transaction.atomic():
            user = User.objects.get(id=user_id, role=User.Role.USER)
            if user.is_active:
                return Response({'error': 'User is not banned'}, status=400)

            user.is_active = True
            user.save()

            transaction.on_commit(
                lambda: send_user_unbanned_email_task.delay(user.id)
            )

            SystemLog.objects.create(
                type='admin',
                message=f'User "{user.email}" unbanned',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return Response({'success': True, 'message': f'User {user.email} unbanned'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def two_factor_login_verify(request):
    temp_token = request.data.get('temp_token')
    code = request.data.get('code')

    if not temp_token or not code:
        return Response({"error": "Nedostaju podaci"}, status=400)

    try:
        user_id = signing.loads(temp_token, salt='2fa-login', max_age=600)
        user = User.objects.get(id=user_id)
    except Exception:
        return Response({"error": "Token nevažeći ili istekao"}, status=400)

    device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
    if not device or not device.verify_token(code):
        return Response({"error": "Pogrešan kod"}, status=400)

    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "role": user.role
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_activity(request):
    logs = ActivityLog.objects.filter(user=request.user)[:20]
    serializer = ActivityLogSerializer(logs, many=True)
    return Response(serializer.data)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.user
        if user.role == 'company' and not user.is_approved:
            return Response({
                'error': 'pending_approval',
                'message': 'Vaš nalog je na čekanju odobrenja administratora.'
            }, status=403)
        has_2fa = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        
        if has_2fa:
            from django.core import signing
            temp_token = signing.dumps(user.id, salt='2fa-login')
            return Response({
                "requires_2fa": True,
                "temp_token": temp_token
            })
        return super().post(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_company_profile(request):
    serializer = CompanyRegisterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = serializer.save()
                send_confirmation_email_task.delay(user.id)
            return Response({"message": "Uspešna registracija! Proverite email."}, status=201)
        except Exception as e:
            return Response({'submit': 'Greška pri slanju emaila. Pokušajte ponovo.'}, status=500)
    return Response(serializer.errors, status=400)


@api_view(['GET'])  
@permission_classes([IsAdmin]) 
def get_users(request):
    users = User.objects.filter(role=User.Role.USER).select_related('company_profile')
    
    paginator = UserPagination()
    paginated_users = paginator.paginate_queryset(users, request)
    serializer = UserListSerializer(paginated_users, many=True)
    
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])  
@permission_classes([AllowAny]) 
def get_companies(request):
    users = User.objects.filter(role=User.Role.COMPANY).select_related('company_profile')
    serializer = UserListSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsUser])
def get_my_profile(request):
    serializer = UserRegisterSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_my_company_profile(request):
    profile = request.user.company_profile
    serializer = CompanyProfileSerializer(profile, context={'request': request})  
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def two_factor_status(request):
    has_2fa = TOTPDevice.objects.filter(user=request.user, confirmed=True).exists()
    return JsonResponse({'enable': has_2fa})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def two_factor_enable(request):
    TOTPDevice.objects.filter(user=request.user, confirmed=False).delete()

    secret = pyotp.random_base32()
    
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        request.user.email,
        issuer_name="infoKOP"
    )

    cache.set(f'2fa_setup_{request.user.id}', secret, timeout=600)

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return JsonResponse({
        'success': True,
        'secret': secret,
        'qr_code': f'data:image/png;base64,{qr_base64}'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def two_factor_verify(request):
    try:
        data = json.loads(request.body)
        code = data.get('code')

        secret = cache.get(f'2fa_setup_{request.user.id}')
        if not secret:
            return JsonResponse({'error': 'Setup expired. Try again.'}, status=400)

        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            TOTPDevice.objects.filter(user=request.user).delete()
            TOTPDevice.objects.create(
                user=request.user,
                name='default',
                confirmed=True,
                key=binascii.hexlify(base64.b32decode(secret + '=' * (-len(secret) % 8))).decode()
            )
            cache.delete(f'2fa_setup_{request.user.id}')
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Invalid verification code'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
        


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def two_factor_disable(request):
    
    try:
        data = json.loads(request.body)
        
        password = data.get('password')
        print(password)
        user = authenticate(request=request, username=request.user.email, password=password)
        print(user)
        if not user:
            return JsonResponse({'error':'Incorrect password'}, status=401)
        
        TOTPDevice.objects.filter(user=request.user).delete()
        
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({'error':str(e)}, status=400)
    
    
    
    
 
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    
    
    
    
    
    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_my_profile(request):
    ActivityLog.objects.create(user=request.user, action='profile', description='Ažuriran profil')
    
    user = request.user
    
    if 'avatar' in request.FILES:
        print("FILES:", request.FILES)
        user.avatar = request.FILES['avatar']
    
    serializer = UserRegisterSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        
        response_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'role': user.role,
            'avatar_url': user.avatar.url if user.avatar else None
        }
        return Response(response_data)
    
    return Response(serializer.errors, status=400)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsCompany])
def company_profile_management(request):
    try:
        company_profile = request.user.company_profile
    except CompanyProfile.DoesNotExist:
        return Response({'error': 'Company profile not found'}, status=404)

    if request.method == 'GET':
        serializer = CompanyProfileSerializer(company_profile, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PATCH':
        if 'cover_photo' in request.FILES:
            company_profile.cover_photo = request.FILES['cover_photo']
        if 'logo' in request.FILES:
            company_profile.logo = request.FILES['logo']

        serializer = CompanyProfileUpdateSerializer(
            company_profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            if 'cover_photo' in request.FILES or 'logo' in request.FILES:
                company_profile.save()

            ActivityLog.objects.create(
                user=request.user,
                action='profile',
                description=f'Ažuriran profil kompanije: {company_profile.company_name}'
            )
            return Response(CompanyProfileSerializer(company_profile).data)

    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsCompany])
def delete_company_image(request, image_type):
    try:
        company_profile = request.user.company_profile
    except CompanyProfile.DoesNotExist:
        return Response({'error': 'Company profile not found'}, status=404)
    
    if image_type not in ['cover', 'logo']:
        return Response({'error': 'Invalid image type. Use "cover" or "logo"'}, status=400)
    
    try:
        if image_type == 'cover':
            if not company_profile.cover_photo:
                return Response({'error': 'No cover photo found'}, status=404)
            company_profile.cover_photo.delete()  
            company_profile.cover_photo = None
            
        elif image_type == 'logo':
            if not company_profile.logo:
                return Response({'error': 'No logo found'}, status=404)
            company_profile.logo.delete()  
            company_profile.logo = None
        
        company_profile.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action='profile',
            description=f'Uklonjena {image_type} fotografija'
        )
        
        return Response({
            'success': True,
            'message': f'{image_type} photo deleted successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


class Register_User_View(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():  
                    user = serializer.save()
                    send_confirmation_email_task.delay(user.id)
                return Response({'message': 'Registracija uspešna! Proverite email.'}, status=201)
            except Exception as e:
                return Response({'submit': 'Greška pri slanju emaila. Pokušajte ponovo.'}, status=500)
        return Response(serializer.errors, status=400)
    
@api_view(["GET"])
@permission_classes([AllowAny])
def verify_email(request):
    uid = request.GET.get('uid')
    token = request.GET.get('token')
    
    try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError):
            return Response({'detail': 'Nevažeći link.'}, status=400)

    if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Link je istekao ili je nevažeći.'}, status=400)

    user.is_active = True
    user.email_confirmed = True
    user.save()

    send_admin_approval_request_task.delay(user.id)

    return Response({'detail': 'Email potvrđen! Čekajte odobrenje administratora.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    user = User.objects.filter(email=email).first()
    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        send_password_reset_email(user, uid, token)  

    return Response({'message': 'Ako nalog postoji, link je poslat na email.'})


UGOSTITELJI_TYPES = ['restoran', 'kafic', 'apres_ski', 'nocni_zivot']

FILTER_MAP = {
    'Restorani': 'restoran',
    'Kafici': 'kafic',
    'Apres-SKI': 'apres_ski',
    'Nocni Zivot': 'nocni_zivot',
}

PARTNER_TYPE_CHOICES = [
    ('hotel', 'Hotel'),
    ('apartman', 'Apartman / Konaci'),
    ('restoran', 'Restoran'),
    ('kafic', 'Kafić'),
    ('apres_ski', 'Après-ski bar'),
    ('nocni_zivot', 'Noćni život'),
    ('aktivnost', 'Aktivnost / Atrakcija'),
    ('ski_skola', 'Ski škola'),
    ('organizator', 'Organizator događaja'),
    ('servis_iznajmljivanje', 'Servis i iznajmljivanje opreme'),
    ('prevoz', 'Prevoz i transfer'),
]


@api_view(['GET'])
@permission_classes([AllowAny])
def get_public_companies(request):
    category = request.query_params.get('category')
    search = request.query_params.get('search', '')

    companies = User.objects.filter(
        role='company',
        is_approved=True,
        company_profile__type__in=UGOSTITELJI_TYPES
    ).select_related('company_profile')

    if search:
        companies = companies.filter(
            company_profile__company_name__icontains=search
        )

    if category and category != 'Svi':
        db_type = FILTER_MAP.get(category)
        if db_type:
            companies = companies.filter(company_profile__type=db_type)

    REVERSE_MAP = {v: k for k, v in FILTER_MAP.items()}

    data = [
        {
            'id': u.id,
            'name': u.company_profile.company_name,
            'category': REVERSE_MAP.get(u.company_profile.type, u.company_profile.type),
            'address': u.company_profile.address,
            'phone': u.phone or None,
        }
        for u in companies if hasattr(u, 'company_profile')
    ]
    return Response(data)

@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError):
        return Response({'error': 'Nevažeći link.'}, status=400)

    if not default_token_generator.check_token(user, token):
        return Response({'error': 'Link je istekao ili je nevažeći.'}, status=400)

    if len(new_password) < 8:
        return Response({'error': 'Lozinka mora imati najmanje 8 karaktera.'}, status=400)

    user.set_password(new_password)
    user.save()
    return Response({'message': 'Lozinka uspešno promenjena.'})