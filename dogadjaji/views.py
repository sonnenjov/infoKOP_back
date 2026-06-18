# dogadjaji/views.py

from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from users.permissions import IsCompany, IsUser
from users.models import ActivityLog
from .models import Dogadjaj, DogadjajReservation
from .serializers import (
    DogadjajSerializer,
    DogadjajCreateSerializer,
    DogadjajReservationSerializer,
    DogadjajReservationStatusUpdateSerializer,
    DogadjajPagination,
)


# ============================================================================
# DOGADJAJI - List and Detail
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_dogadjaji(request):
    """Get all active events with optional filters"""
    queryset = Dogadjaj.objects.filter(is_active=True).select_related('company')

    kategorija = request.query_params.get('kategorija')
    if kategorija and kategorija != 'svi':
        queryset = queryset.filter(kategorija=kategorija)

    season = request.query_params.get('season')
    if season and season != 'all_year':
        queryset = queryset.filter(season=season)

    od_datuma = request.query_params.get('od_datuma')
    if od_datuma:
        queryset = queryset.filter(datum_pocetka__gte=od_datuma)

    do_datuma = request.query_params.get('do_datuma')
    if do_datuma:
        queryset = queryset.filter(datum_pocetka__lte=do_datuma)

    paginator = DogadjajPagination()
    paginated = paginator.paginate_queryset(queryset, request)
    serializer = DogadjajSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_dogadjaj_detail(request, slug):
    dogadjaj = get_object_or_404(Dogadjaj, slug=slug, is_active=True)
    serializer = DogadjajSerializer(dogadjaj)
    return Response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_my_dogadjaji(request):
    """Get all events for the logged-in company"""
    dogadjaji = Dogadjaj.objects.filter(company=request.user.company_profile)
    serializer = DogadjajSerializer(dogadjaji, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCompany])
def create_dogadjaj(request):
    """Create a new event"""
    serializer = DogadjajCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        dogadjaj = serializer.save()
        return Response(DogadjajSerializer(dogadjaj).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsCompany])
def update_dogadjaj(request, pk):
    """Update an event"""
    dogadjaj = get_object_or_404(Dogadjaj, pk=pk, company=request.user.company_profile)
    serializer = DogadjajCreateSerializer(
        dogadjaj, data=request.data, partial=True, context={'request': request}
    )
    if serializer.is_valid():
        dogadjaj = serializer.save()
        return Response(DogadjajSerializer(dogadjaj).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsCompany])
def delete_dogadjaj(request, pk):
    """Delete an event"""
    dogadjaj = get_object_or_404(Dogadjaj, pk=pk, company=request.user.company_profile)
    dogadjaj.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# DOGADJAJ RESERVATIONS - User Operations
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
def create_dogadjaj_reservation(request):
    """Create a new event reservation - only for regular users"""
    serializer = DogadjajReservationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        rezervacija = serializer.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action=ActivityLog.ActionType.RESERVATION,
            description=f"Nova rezervacija za event '{rezervacija.dogadjaj.naziv}' ({rezervacija.broj_karata} karata)"
        )
        
        return Response(DogadjajReservationSerializer(rezervacija).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsUser])
def get_my_dogadjaj_reservations(request):
    """Get all event reservations for the logged-in user"""
    rezervacije = DogadjajReservation.objects.filter(user=request.user).select_related(
        'dogadjaj', 'dogadjaj__company'
    )
    serializer = DogadjajReservationSerializer(rezervacije, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsUser])
def cancel_dogadjaj_reservation(request, pk):
    """Cancel an event reservation - user can only cancel their own"""
    rezervacija = get_object_or_404(DogadjajReservation, pk=pk, user=request.user)
    
    # Only allow cancellation if not already cancelled or completed
    if rezervacija.status in [DogadjajReservation.Status.CANCELLED, DogadjajReservation.Status.COMPLETED]:
        return Response(
            {'error': 'Ova rezervacija ne može biti otkazana'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = rezervacija.status
    rezervacija.status = DogadjajReservation.Status.CANCELLED
    rezervacija.save()
    
    # Log activity
    ActivityLog.objects.create(
        user=request.user,
        action=ActivityLog.ActionType.RESERVATION,
        description=f"Otkazana rezervacija za event '{rezervacija.dogadjaj.naziv}'"
    )
    
    return Response(DogadjajReservationSerializer(rezervacija).data)


# ============================================================================
# DOGADJAJ RESERVATIONS - Company Operations
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_company_dogadjaj_reservations(request):
    """Get all event reservations for company's events"""
    rezervacije = DogadjajReservation.objects.filter(
        dogadjaj__company=request.user.company_profile
    ).select_related('dogadjaj', 'user')
    serializer = DogadjajReservationSerializer(rezervacije, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsCompany])
def update_dogadjaj_reservation_status(request, pk):
    """Update event reservation status - company can confirm/reject"""
    rezervacija = get_object_or_404(
        DogadjajReservation, pk=pk, dogadjaj__company=request.user.company_profile
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
        description=f"Status rezervacije #{rezervacija.id} za event promenjen sa {old_status} na {new_status}"
    )
    
    return Response(DogadjajReservationSerializer(rezervacija).data)


# ============================================================================
# DOGADJAJ DASHBOARD
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_company_dogadjaj_dashboard_stats(request):
    """Get dashboard statistics for company's events"""
    company = request.user.company_profile
    
    # Summary stats
    all_reservations = DogadjajReservation.objects.filter(dogadjaj__company=company)
    confirmed_reservations = all_reservations.filter(status=DogadjajReservation.Status.CONFIRMED)
    
    summary = {
        'total_reservations': all_reservations.count(),
        'pending_reservations': all_reservations.filter(status=DogadjajReservation.Status.PENDING).count(),
        'confirmed_reservations': confirmed_reservations.count(),
        'cancelled_reservations': all_reservations.filter(status=DogadjajReservation.Status.CANCELLED).count(),
        'total_revenue': float(confirmed_reservations.aggregate(Sum('total_price'))['total_price__sum'] or 0),
        'total_tickets_sold': confirmed_reservations.aggregate(Sum('broj_karata'))['broj_karata__sum'] or 0,
    }
    
    # Monthly breakdown
    monthly_data = confirmed_reservations.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_price'),
        reservations=Count('id'),
        tickets=Sum('broj_karata')
    ).order_by('month')
    
    # Events with their reservations
    events_stats = []
    for event in company.dogadjaji.all():
        event_res = event.rezervacije.filter(status=DogadjajReservation.Status.CONFIRMED)
        events_stats.append({
            'event_id': event.id,
            'event_name': event.naziv,
            'event_date': event.datum_pocetka,
            'total_revenue': float(event_res.aggregate(Sum('total_price'))['total_price__sum'] or 0),
            'total_tickets': event_res.aggregate(Sum('broj_karata'))['broj_karata__sum'] or 0,
            'reservations_count': event_res.count(),
        })
    
    return Response({
        'company': {
            'id': company.id,
            'name': company.company_name,
            'type': company.type,
        },
        'summary': summary,
        'monthly_data': monthly_data,
        'events_stats': events_stats,
    })