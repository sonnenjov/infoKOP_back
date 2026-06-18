# smestaj/views.py

from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from users.permissions import IsCompany, IsUser
from users.models import ActivityLog
from users.serializers import PageNumberPagination
from .models import Smestaj, SmestajReservation
from .serializers import (
    SmestajSerializer,
    SmestajCreateSerializer,
    SmestajReservationSerializer,
    SmestajReservationStatusUpdateSerializer,
    SmestajPagination,
)


# ============================================================================
# SMESTAJI - List and Detail
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_smestaji(request):
    """Get all active accommodations with optional filters"""
    smestaji = Smestaj.objects.filter(is_active=True).select_related('company')

    season = request.query_params.get('season')
    if season:
        smestaji = smestaji.filter(season__in=[season, 'all_year'])

    tip = request.query_params.get('tip')
    if tip:
        smestaji = smestaji.filter(tip=tip)

    max_udaljenost = request.query_params.get('max_udaljenost')
    if max_udaljenost:
        smestaji = smestaji.filter(udaljenost_od_staza__lte=max_udaljenost)

    max_cena = request.query_params.get('max_cena')
    if max_cena:
        smestaji = smestaji.filter(cena_po_nocenju__lte=max_cena)

    min_cena = request.query_params.get('min_cena')
    if min_cena:
        smestaji = smestaji.filter(cena_po_nocenju__gte=min_cena)

    company_slug = request.query_params.get('company')
    if company_slug:
        smestaji = smestaji.filter(company__slug=company_slug)

    paginator = SmestajPagination()
    paginated = paginator.paginate_queryset(smestaji, request)
    serializer = SmestajSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_smestaj_detail(request, slug):
    """Get single accommodation detail"""
    smestaj = get_object_or_404(Smestaj, slug=slug, is_active=True)
    serializer = SmestajSerializer(smestaj)
    return Response(serializer.data)


# ============================================================================
# SMESTAJI - Company Management
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_my_smestaji(request):
    """Get all accommodations for the logged-in company"""
    smestaji = Smestaj.objects.filter(company=request.user.company_profile)
    serializer = SmestajSerializer(smestaji, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCompany])
def create_smestaj(request):
    """Create a new accommodation"""
    serializer = SmestajCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        smestaj = serializer.save()
        return Response(SmestajSerializer(smestaj).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsCompany])
def update_smestaj(request, pk):
    """Update an accommodation"""
    smestaj = get_object_or_404(Smestaj, pk=pk, company=request.user.company_profile)
    serializer = SmestajCreateSerializer(
        smestaj, data=request.data, partial=True, context={'request': request}
    )
    if serializer.is_valid():
        smestaj = serializer.save()
        return Response(SmestajSerializer(smestaj).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsCompany])
def delete_smestaj(request, pk):
    """Delete an accommodation"""
    smestaj = get_object_or_404(Smestaj, pk=pk, company=request.user.company_profile)
    smestaj.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# SMESTAJ RESERVATIONS - User Operations
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
def create_smestaj_reservation(request):
    """Create a new accommodation reservation - only for regular users"""
    serializer = SmestajReservationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        rezervacija = serializer.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action=ActivityLog.ActionType.RESERVATION,
            description=f"Nova rezervacija za {rezervacija.smestaj.naziv} od {rezervacija.check_in} do {rezervacija.check_out}"
        )
        
        return Response(SmestajReservationSerializer(rezervacija).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsUser])
def get_my_smestaj_reservations(request):
    """Get all accommodation reservations for the logged-in user"""
    rezervacije = SmestajReservation.objects.filter(user=request.user).select_related(
        'smestaj', 'smestaj__company'
    )
    serializer = SmestajReservationSerializer(rezervacije, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsUser])
def cancel_smestaj_reservation(request, pk):
    """Cancel an accommodation reservation - user can only cancel their own"""
    rezervacija = get_object_or_404(SmestajReservation, pk=pk, user=request.user)
    
    # Only allow cancellation if not already cancelled or completed
    if rezervacija.status in [SmestajReservation.Status.CANCELLED, SmestajReservation.Status.COMPLETED]:
        return Response(
            {'error': 'Ova rezervacija ne može biti otkazana'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = rezervacija.status
    rezervacija.status = SmestajReservation.Status.CANCELLED
    rezervacija.save()
    
    # Log activity
    ActivityLog.objects.create(
        user=request.user,
        action=ActivityLog.ActionType.RESERVATION,
        description=f"Otkazana rezervacija za {rezervacija.smestaj.naziv}"
    )
    
    return Response(SmestajReservationSerializer(rezervacija).data)


# ============================================================================
# SMESTAJ RESERVATIONS - Company Operations
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_company_smestaj_reservations(request):
    """Get all accommodation reservations for company's properties"""
    rezervacije = SmestajReservation.objects.filter(
        smestaj__company=request.user.company_profile
    ).select_related('smestaj', 'user')
    serializer = SmestajReservationSerializer(rezervacije, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsCompany])
def update_smestaj_reservation_status(request, pk):
    """Update accommodation reservation status - company can confirm/reject"""
    rezervacija = get_object_or_404(
        SmestajReservation, pk=pk, smestaj__company=request.user.company_profile
    )
    
    new_status = request.data.get('status')
    if not new_status:
        return Response(
            {'error': 'Status je obavezan'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = rezervacija.status
    rezervacija.status = new_status
    rezervacija.save()
    
    # Log for company
    ActivityLog.objects.create(
        user=request.user,
        action=ActivityLog.ActionType.RESERVATION,
        description=f"Status rezervacije #{rezervacija.id} promenjen sa {old_status} na {new_status}"
    )
    
    return Response(SmestajReservationSerializer(rezervacija).data)


# ============================================================================
# SMESTAJ DASHBOARD
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_company_dashboard_stats(request):
    """Get dashboard statistics for company's accommodations"""
    company = request.user.company_profile
    
    # Summary stats
    all_reservations = SmestajReservation.objects.filter(smestaj__company=company)
    confirmed_reservations = all_reservations.filter(status=SmestajReservation.Status.CONFIRMED)
    
    summary = {
        'total_reservations': all_reservations.count(),
        'pending_reservations': all_reservations.filter(status=SmestajReservation.Status.PENDING).count(),
        'confirmed_reservations': confirmed_reservations.count(),
        'cancelled_reservations': all_reservations.filter(status=SmestajReservation.Status.CANCELLED).count(),
        'total_revenue': float(confirmed_reservations.aggregate(Sum('total_price'))['total_price__sum'] or 0),
        'total_guests': (
            confirmed_reservations.aggregate(
                total=Sum('broj_odraslih') + Sum('broj_dece')
            )['total'] or 0
        ),
    }
    
    # Monthly breakdown
    monthly_data = confirmed_reservations.annotate(
        month=TruncMonth('check_in')
    ).values('month').annotate(
        revenue=Sum('total_price'),
        reservations=Count('id'),
        guests=Sum('broj_odraslih') + Sum('broj_dece')
    ).order_by('month')
    
    # Properties with their stats
    properties_stats = []
    for prop in company.smestaji.all():
        prop_res = prop.rezervacije.filter(status=SmestajReservation.Status.CONFIRMED)
        properties_stats.append({
            'property_id': prop.id,
            'property_name': prop.naziv,
            'property_type': prop.tip,
            'total_revenue': float(prop_res.aggregate(Sum('total_price'))['total_price__sum'] or 0),
            'total_guests': (
                prop_res.aggregate(
                    total=Sum('broj_odraslih') + Sum('broj_dece')
                )['total'] or 0
            ),
            'reservations_count': prop_res.count(),
        })
    
    return Response({
        'company': {
            'id': company.id,
            'name': company.company_name,
            'type': company.type,
        },
        'summary': summary,
        'monthly_data': monthly_data,
        'properties_stats': properties_stats,
    })