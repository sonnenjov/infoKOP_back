from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.utils.html import strip_tags
from newsletter.models import Newsletter, Subscription
from .models import Vest

@receiver(pre_save, sender=Vest)
def store_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._previous_status = Vest.objects.get(pk=instance.pk).status
        except Vest.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, sender=Vest)
def notify_subscribers(sender, instance, created, **kwargs):
    previous = getattr(instance, '_previous_status', None)
    
    if instance.status == 'objavljeno' and previous != 'objavljeno':
        try:
            newsletter = Newsletter.objects.get(slug='infokop-newsletter')
            subscriber_emails = list(
                Subscription.objects.filter(
                    newsletter=newsletter,
                    subscribed=True
                ).values_list('email_field', flat=True)
            )
            
            if not subscriber_emails:
                return
            
            clean_text = strip_tags(instance.text)
            excerpt = clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
            full_url = f"http://192.168.1.6:5173/vesti/{instance.id}"
            
            send_mail(
                subject=f"Nova vest: {instance.title}",
                message=f"{excerpt}\n\nPročitajte ceo članak: {full_url}",
                from_email='infokopapp@gmail.com',
                recipient_list=subscriber_emails,
                fail_silently=False,
            )
        except Newsletter.DoesNotExist:
            pass