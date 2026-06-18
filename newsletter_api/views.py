from newsletter.models import Newsletter, Subscription
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from vesti.models import Vest 
from django.utils.html import strip_tags
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def subscribe(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email je obavezan'}, status=400)
    
    try:
        newsletter = Newsletter.objects.get(slug='infokop-newsletter')
        subscription, created = Subscription.objects.get_or_create(
            newsletter=newsletter,
            email_field=email
        )
        subscription.subscribed = True
        subscription.save()
        return Response({'success': True, 'message': 'Uspešno ste se prijavili'})
    except Newsletter.DoesNotExist:
        return Response({'error': 'Newsletter not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)
      
      
      
      
      
