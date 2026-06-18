import uuid
from django.utils import timezone
from django.utils.timezone import now

from ski_pasovi.serializers import SkiPassSerializer
from .utils.qr_utils import generate_qr_base64
from rest_framework.decorators import api_view, permission_classes  
from rest_framework.permissions import IsAuthenticated
from .models import SkiPass
from rest_framework.response import Response
from datetime import timedelta

PASS_DURATIONS = {
    'daily': timedelta(days=1),
    'daily3': timedelta(days=3),
    'weekly': timedelta(weeks=1),
    'seasonal': timedelta(days=180),
}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_skipass(request):
    existing = SkiPass.objects.filter(
        user=request.user,
        is_used=False,
        valid_until__gt=timezone.now()
    ).first()
    
    if existing:
        return Response(
            {'error': 'Već imate aktivan ski pass. Ne možete kupiti novi dok trenutni ne istekne.'},
            status=400
        )

    pass_type = request.data.get('pass_type')
    if pass_type not in PASS_DURATIONS:
        return Response({'error': 'Invalid pass type'}, status=400)

    code = 'SKI-' + str(uuid.uuid4().hex[:10].upper())
    valid_until = timezone.now() + PASS_DURATIONS[pass_type]

    ski_pass = SkiPass.objects.create(
        user=request.user,
        code=code,
        pass_type=pass_type,
        valid_until=valid_until,
        price_paid=request.data.get('price_paid'),
    )

    serializer = SkiPassSerializer(ski_pass)
    return Response(serializer.data, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_passes(request):
    passes = SkiPass.objects.filter(user=request.user).order_by('-purchased_at')
    serializer = SkiPassSerializer(passes, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_skipass(request):
    code = request.data.get('code')
    if not code:
        return Response({'error': 'Code is required'}, status=400)

    try:
        ski_pass = SkiPass.objects.get(code=code)
    except SkiPass.DoesNotExist:
        return Response({'valid': False, 'error': 'Pass not found'}, status=404)

    if not ski_pass.is_valid():
        return Response({'valid': False, 'error': 'Already used or expired'})

    ski_pass.is_used = True
    ski_pass.used_at = timezone.now()
    ski_pass.save()

    return Response({'valid': True, 'pass_type': ski_pass.pass_type, 'user': ski_pass.user.email})




@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_skipass(request, pk):
    try:
        ski_pass = SkiPass.objects.get(pk=pk)
    except SkiPass.DoesNotExist:
        return Response({'error': 'Pass not found'}, status=404)
    if ski_pass.user != request.user:
        return Response({'error': 'Not your pass'}, status=403)
    ski_pass.delete()
    return Response(status=204)