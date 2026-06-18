from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from smestaj.models import SmestajReservation
from smestaj.serializers import SmestajReservationSerializer, SmestajReservationStatusUpdateSerializer
from users.models import ActivityLog
from users.permissions import IsCompany, IsUser
from .models import Activity, Reservation
from .serializers import (
    ActivitySerializer,
    ActivityCreateSerializer,
    ReservationSerializer,
    ReservationStatusUpdateSerializer,
    ActivityPagination,
)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsCompany])
def update_smestaj_reservation_status(request, pk):
    rezervacija = get_object_or_404(
        SmestajReservation, pk=pk, smestaj__company=request.user.company_profile
    )
    serializer = SmestajReservationStatusUpdateSerializer(rezervacija, data=request.data, partial=True)
    if serializer.is_valid():
        new_status = serializer.validated_data.get('status')
        old_status = rezervacija.status
        
        if new_status == SmestajReservation.Status.COMPLETED and old_status != SmestajReservation.Status.COMPLETED:
            if not rezervacija.revenue_updated:
                company = request.user.company_profile
                total_guests = rezervacija.broj_odraslih + rezervacija.broj_dece
                company.update_revenue(rezervacija.total_price, total_guests)
                
                rezervacija.revenue_updated = True
                rezervacija.save()
        
        elif old_status == SmestajReservation.Status.COMPLETED and new_status != SmestajReservation.Status.COMPLETED:
            if rezervacija.revenue_updated:
                company = request.user.company_profile
                company.total_revenue -= rezervacija.total_price
                company.total_reservations -= 1
                company.total_guests -= (rezervacija.broj_odraslih + rezervacija.broj_dece)
                company.save()
                
                rezervacija.revenue_updated = False
                rezervacija.save()
        
        serializer.save()
        return Response(SmestajReservationSerializer(rezervacija).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_activities(request):
    activities = Activity.objects.filter(is_active=True).select_related('company')

    season = request.query_params.get('season')
    if season:
        activities = activities.filter(season__in=[season, 'all_year'])

    company_slug = request.query_params.get('company')
    if company_slug:
        activities = activities.filter(company__slug=company_slug)

    paginator = ActivityPagination()
    paginated_activities = paginator.paginate_queryset(activities, request)
    serializer = ActivitySerializer(paginated_activities, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_activity_detail(request, slug):
    activity = get_object_or_404(Activity, slug=slug, is_active=True)
    serializer = ActivitySerializer(activity)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_my_activities(request):
    activities = Activity.objects.filter(company=request.user.company_profile)
    serializer = ActivitySerializer(activities, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsUser])
def get_my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).select_related('activity', 'activity__company')
    serializer = ReservationSerializer(reservations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompany])
def get_company_reservations(request):
    reservations = Reservation.objects.filter(
        activity__company=request.user.company_profile
    ).select_related('activity', 'user')
    serializer = ReservationSerializer(reservations, many=True)
    return Response(serializer.data)




@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCompany])
def create_activity(request):
    serializer = ActivityCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        activity = serializer.save()
        return Response(ActivitySerializer(activity).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
def create_reservation(request):
    ActivityLog.objects.create(user=request.user, action='reservations', description='Napravljena rezervacija')
    serializer = ReservationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        reservation = serializer.save()
        return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsCompany])
def update_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk, company=request.user.company_profile)
    serializer = ActivityCreateSerializer(
        activity, data=request.data, partial=True, context={'request': request}
    )
    if serializer.is_valid():
        activity = serializer.save()
        return Response(ActivitySerializer(activity).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsUser])
def cancel_reservation(request, pk):
    ActivityLog.objects.create(user=request.user, action='reservations', description='Otkazana rezervacija')
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    reservation.status = Reservation.Status.CANCELLED
    reservation.save()
    serializer = ReservationSerializer(reservation)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsCompany])
def update_reservation_status(request, pk):
    reservation = get_object_or_404(
        Reservation, pk=pk, activity__company=request.user.company_profile
    )
    serializer = ReservationStatusUpdateSerializer(reservation, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(ReservationSerializer(reservation).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsCompany])
def delete_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk, company=request.user.company_profile)
    activity.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)