from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
def send_confirmation_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    frontend_url = "http://192.168.1.6:5173"  
    verification_link = f"{frontend_url}/verify-email?uid={uid}&token={token}"
    subject = "Potvrdite vaš email"
    message = f"""
    Poštovani/a,
    Hvala vam na registraciji. Kliknite na sledeći link da potvrdite vaš email:
    {verification_link}
    Ako niste vi napravili nalog, ignorišite ovaj email.
    Srdačan pozdrav,
    InfoKOP tim
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
  
def send_admin_approval_request(user):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admins = User.objects.filter(role='admin').values_list('email', flat=True)
    if not admins:
        return
    send_mail(
        subject=f'Novi korisnik čeka odobrenje — {user.email}',
        message=f'''Novi korisnik je potvrdio email i čeka odobrenje.
Email: {user.email}
Ime: {user.first_name} {user.last_name}
Rola: {user.role}
Odobrite nalog u admin panelu: http://192.168.1.6:5173/admin/dashboard
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=list(admins),
        fail_silently=False,
    )
    
    
    
def send_approval_email(user, company):
    send_mail(
        subject='infoKOP — Vaš nalog je odobren!',
        message=f'''
Poštovani {company.company_name},
Vaš poslovni nalog na infoKOP platformi je uspešno odobren.
Sada možete da se prijavite i počnete da upravljate svojim profilom:
http://192.168.1.6:5173/login
Hvala što ste deo infoKOP zajednice!
Tim infoKOP
        ''',
        from_email='infokopapp@gmail.com',
        recipient_list=[user.email],
        fail_silently=False,
    )
    
    
    
    
    
    
def send_rejection_email(user, company, reason):
    send_mail(
        subject='infoKOP — Vaš zahtev za registraciju',
        message=f'''
Poštovani {company.company_name},
Nažalost, Vaš zahtev za registraciju na infoKOP platformi nije odobren.
Razlog: {reason if reason else 'Nije naveden razlog.'}
Ukoliko smatrate da je ovo greška ili želite da ispravite dokumentaciju, možete se ponovo registrovati na:
http://192.168.1.6:5173/partner/register
Tim infoKOP
        ''',
        from_email='infokopapp@gmail.com',
        recipient_list=[user.email],
        fail_silently=False,
    )
    
    
    
    
    
def send_password_reset_email(user, uid, token):
    reset_link = f"http://192.168.1.6:5173/reset-password?uid={uid}&token={token}"
    
    send_mail(
        subject="Resetovanje lozinke - infoKOP",
        message=f"Kliknite na link da resetujete lozinku:\n\n{reset_link}\n\nLink važi 1 sat.",
        from_email="noreply@infokop.rs",
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_user_approval_email(user):
    send_mail(
        subject='infoKOP — Vaš nalog je odobren!',
        message=f'''
Poštovani {user.first_name},
Vaš nalog na infoKOP platformi je uspešno odobren.
Sada možete da se prijavite i koristite platformu:
http://192.168.1.6:5173/login
Hvala što ste deo infoKOP zajednice!
Tim infoKOP
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_user_rejection_email(user, reason):
    send_mail(
        subject='infoKOP — Vaš zahtev za registraciju',
        message=f'''
Poštovani {user.first_name},
Nažalost, Vaš zahtev za registraciju na infoKOP platformi nije odobren.
Razlog: {reason if reason else 'Nije naveden razlog.'}
Ukoliko smatrate da je ovo greška, možete se ponovo registrovati na:
http://192.168.1.6:5173/register
Tim infoKOP
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_user_banned_email(user, reason):
    send_mail(
        subject='infoKOP — Vaš nalog je suspendovan',
        message=f'''
Poštovani {user.first_name},
Vaš nalog na infoKOP platformi je suspendovan od strane administratora.
Razlog: {reason if reason else 'Nije naveden razlog.'}
Ukoliko smatrate da je ovo greška, kontaktirajte podršku na infokopapp@gmail.com.
Tim infoKOP
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_user_unbanned_email(user):
    send_mail(
        subject='infoKOP — Vaš nalog je ponovo aktiviran',
        message=f'''
Poštovani {user.first_name},
Vaš nalog na infoKOP platformi je ponovo aktiviran. Možete se prijaviti:
http://192.168.1.6:5173/login
Tim infoKOP
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )