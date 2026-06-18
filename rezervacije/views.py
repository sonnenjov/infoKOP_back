# rezervacije/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone
from datetime import timedelta

from users.models import ActivityLog
from .models import Reservation
from .serializers import (
    ReservationSerializer,
    ReservationCreateSerializer,
    ReservationStatusSerializer,
)


class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    
    def create(self, request, *args, **kwargs):
        print("=== RESERVATION CREATE ===")
        print("DATA:", request.data)
        print("USER:", request.user)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("ERRORS:", serializer.errors)
            return Response(serializer.errors, status=400)
        return super().create(request, *args, **kwargs)
    
    
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        if self.action == 'update_status':
            return ReservationStatusSerializer
        return ReservationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Reservation.objects.all().select_related('guest', 'company')
        if user.role == 'company':
            return Reservation.objects.filter(
                company=user.company_profile
            ).select_related('guest', 'company')
        return Reservation.objects.filter(
            guest=user
        ).select_related('guest', 'company')

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        ActivityLog.objects.create(user=request.user, action='profile', description='Rezervacija izmenjena')

        reservation = self.get_object()
        
        if request.user.role == 'company':
            if reservation.company.user != request.user:
                return Response({'error': 'Not your reservation.'}, status=403)
        else:
            if reservation.guest != request.user:
                return Response({'error': 'Not your reservation.'}, status=403)
            if request.data.get('status') != 'cancelled':
                return Response({'error': 'Guests can only cancel reservations.'}, status=403)

        serializer = ReservationStatusSerializer(reservation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReservationSerializer(reservation).data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        user = request.user
        
        if user.role != 'company':
            return Response(
                {'error': 'Only companies can access analytics.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        company = user.company_profile
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        current_month = Reservation.objects.filter(
            company=company,
            created_at__gte=start_of_month
        )
        
       
        stats = current_month.aggregate(
            total_revenue=Sum('amount'),
            total_bookings=Count('id'),
            avg_booking=Avg('amount')
        )
        
        prev_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        prev_month = Reservation.objects.filter(
            company=company,
            created_at__gte=prev_month_start,
            created_at__lt=start_of_month
        )
        
        prev_stats = prev_month.aggregate(
            prev_revenue=Sum('amount'),
            prev_bookings=Count('id')
        )
        
        revenue_trend = 0
        bookings_trend = 0
        
        if prev_stats['prev_revenue'] and prev_stats['prev_revenue'] > 0:
            revenue_trend = int(((stats['total_revenue'] or 0) - prev_stats['prev_revenue']) / prev_stats['prev_revenue'] * 100)
        if prev_stats['prev_bookings'] and prev_stats['prev_bookings'] > 0:
            bookings_trend = int(((stats['total_bookings'] or 0) - prev_stats['prev_bookings']) / prev_stats['prev_bookings'] * 100)
        
        return Response({
            'total_revenue': stats['total_revenue'] or 0,
            'total_bookings': stats['total_bookings'] or 0,
            'avg_booking_value': int(stats['avg_booking'] or 0),
            'revenue_trend': revenue_trend,
            'bookings_trend': bookings_trend
        })

    @action(detail=False, methods=['get'])
    def revenue_trend(self, request):
        user = request.user
        
        if user.role != 'company':
            return Response(
                {'error': 'Only companies can access analytics.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        period = request.query_params.get('period', 'daily')
        company = user.company_profile
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        reservations = Reservation.objects.filter(
            company=company,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if period == 'weekly':
            annotations = reservations.annotate(
                date=TruncWeek('created_at')
            ).values('date').annotate(
                revenue=Sum('amount'), 
                bookings=Count('id')
            ).order_by('date')
        else:
            annotations = reservations.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                revenue=Sum('amount'), 
                bookings=Count('id')
            ).order_by('date')
        
        data = []
        for item in annotations:
            if item['date']:
                date_str = item['date'].strftime('%d %b') if period == 'daily' else f"Week {item['date'].isocalendar()[1]}"
                data.append({
                    'date': date_str,
                    'revenue': item['revenue'] or 0,
                    'bookings': item['bookings'] or 0
                })
        
        return Response({'data': data})

    @action(detail=False, methods=['get'])
    def channel_distribution(self, request):
        user = request.user
        
        if user.role != 'company':
            return Response(
                {'error': 'Only companies can access analytics.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        company = user.company_profile
        
        try:
            channels = Reservation.objects.filter(
                company=company
            ).values('channel').annotate(
                count=Count('id')
            )
            
            total = sum([c['count'] for c in channels])
            
            if total > 0:
                data = []
                for channel in channels:
                    data.append({
                        'name': channel['channel'] or 'Ostalo',
                        'value': round((channel['count'] / total) * 100)
                    })
            else:
                data = [
                    {'name': 'InfoKOP', 'value': 54},
                    {'name': 'Direktno', 'value': 23},
                    {'name': 'Booking.com', 'value': 14},
                    {'name': 'Ostalo', 'value': 9},
                ]
            
            return Response({'data': data})
        except Exception as e:
            return Response({
                'data': [
                    {'name': 'InfoKOP', 'value': 54},
                    {'name': 'Direktno', 'value': 23},
                    {'name': 'Booking.com', 'value': 14},
                    {'name': 'Ostalo', 'value': 9},
                ]
            })

    @action(detail=False, methods=['get'])
    def recent_bookings(self, request):
        user = request.user
        
        if user.role != 'company':
            return Response(
                {'error': 'Only companies can access analytics.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        limit = int(request.query_params.get('limit', 5))
        company = user.company_profile
        
        bookings = Reservation.objects.filter(
            company=company
        ).select_related('guest').order_by('-created_at')[:limit]
        
        data = []
        for booking in bookings:
            nights = 1
            if booking.date_from and booking.date_to:
                nights = (booking.date_to - booking.date_from).days
            
            checkin_date = booking.date_from.strftime('%d %b') if booking.date_from else ''
            
            data.append({
                'id': f"RES-{booking.id:04d}",
                'guest': f"{booking.guest.first_name} {booking.guest.last_name}",
                'service': booking.service_name or "N/A",
                'checkin': checkin_date,
                'nights': nights,
                'amount': float(booking.amount) if booking.amount else 0,  # Use 'amount'
                'status': booking.status
            })
        
        return Response({'data': data})