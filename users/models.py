from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        username = email.split('@')[0]
        extra_fields.setdefault('username', username)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


def get_user_upload_folder(instance, filename):
    return f"users/{instance.role}"


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        COMPANY = 'company', 'Company'
        REPORTER = 'reporter', 'Reporter'
        ADMIN = 'admin', 'Admin'
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.USER)
    phone = models.CharField(max_length=20, blank=True)
    objects = CustomUserManager()
    avatar = CloudinaryField(
        'image', 
        folder='infokop/users/avatars',
        null=True,
        blank=True
    )
    email_confirmed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class CompanyProfile(models.Model):
    PARTNER_TYPE_CHOICES = [
        ('hotel', 'Hotel'),
        ('apartman', 'Apartman / Konaci'),
        ('restoran', 'Restoran'),
        ('kafic', 'Kafić'),
        ('apres_ski', 'Après-ski bar'),
        ('aktivnost', 'Aktivnost / Atrakcija'),
        ('ski_skola', 'Ski škola'),
        ('organizator', 'Organizator događaja'),
        ('servis_iznajmljivanje', 'Servis i iznajmljivanje opreme'),
        ('prevoz', 'Prevoz i transfer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile', null=True, blank=True)
    type = models.CharField(max_length=50, choices=PARTNER_TYPE_CHOICES, default='hotel')
    company_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    pib = models.CharField(max_length=50, unique=True, null=True, blank=True)
    slug = models.SlugField(max_length=255, blank=True)
    
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_reservations = models.IntegerField(default=0)
    total_guests = models.IntegerField(default=0)
    monthly_revenue = models.JSONField(default=dict, blank=True)
    yearly_revenue = models.JSONField(default=dict, blank=True)
    
    cover_photo = CloudinaryField(
        'image',
        folder='infokop/partners/covers',
        null=True,
        blank=True
    )
    logo = CloudinaryField(
        'image',
        folder='infokop/partners/logos',
        null=True,
        blank=True
    )

    def update_revenue(self, amount, guests=0):
        from django.utils import timezone
        from decimal import Decimal
        
        self.total_revenue += Decimal(str(amount))
        self.total_reservations += 1
        self.total_guests += guests
        
        current_month = timezone.now().strftime('%Y-%m')
        if current_month in self.monthly_revenue:
            self.monthly_revenue[current_month] += float(amount)
        else:
            self.monthly_revenue[current_month] = float(amount)
        
        current_year = timezone.now().strftime('%Y')
        if current_year in self.yearly_revenue:
            self.yearly_revenue[current_year] += float(amount)
        else:
            self.yearly_revenue[current_year] = float(amount)
        
        self.save(update_fields=['total_revenue', 'total_reservations', 'total_guests', 'monthly_revenue', 'yearly_revenue'])
    
    def save(self, *args, **kwargs):
        if not self.slug and self.company_name:
            base_slug = slugify(self.company_name)
            slug = base_slug
            counter = 1
            while CompanyProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.company_name or str(self.user)


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} (${self.base_price})"


class CompanyOfferedService(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='offered_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    max_capacity = models.IntegerField(default=1)
    requires_advance_booking_days = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['company', 'service']
    
    @property
    def effective_price(self):
        return self.custom_price if self.custom_price is not None else self.service.base_price
    
    def __str__(self):
        return f"{self.company.company_name} - {self.service.name} (${self.effective_price})"


class ActivityLog(models.Model):
    class ActionType(models.TextChoices):
        LOGIN = 'login', 'Prijava'
        RESERVATION = 'reservation', 'Rezervacija'
        SKIPASS = 'skipass', 'Ski Pass'
        PROFILE = 'profile', 'Profil'
        PASSWORD = 'password', 'Lozinka'
        OTHER = 'other', 'Ostalo'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ActionType.choices)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.action} — {self.created_at}"