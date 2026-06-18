from django.conf import settings
from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from users.models import CompanyProfile


class Smestaj(models.Model):
    class TipSmestaja(models.TextChoices):
        HOTEL = 'hotel', 'Hotel'
        APARTMAN = 'apartman', 'Apartman'
        VILA = 'vila', 'Vila & Brvnara'

    class Season(models.TextChoices):
        SUMMER = 'summer', 'Summer'
        WINTER = 'winter', 'Winter'
        ALL_YEAR = 'all_year', 'All Year'

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='smestaji'
    )
    naziv = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    opis = models.TextField(blank=True)
    tip = models.CharField(max_length=20, choices=TipSmestaja.choices, default=TipSmestaja.HOTEL)
    season = models.CharField(max_length=10, choices=Season.choices, default=Season.ALL_YEAR)
    cena_po_nocenju = models.DecimalField(max_digits=10, decimal_places=2)
    udaljenost_od_staza = models.IntegerField(default=0, help_text="Udaljenost u metrima")
    kapacitet = models.IntegerField(default=1)
    image = CloudinaryField(
        'image',
        folder='infokop/smestaj',
        null=True,
        blank=True
    )

    ima_spa = models.BooleanField(default=False)
    ima_bazen = models.BooleanField(default=False)
    ski_in_ski_out = models.BooleanField(default=False)
    ima_restoran = models.BooleanField(default=False)
    ima_parking = models.BooleanField(default=False)
    ima_wifi = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.naziv:
            base_slug = slugify(self.naziv)
            slug = base_slug
            counter = 1
            while Smestaj.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.naziv} - {self.company.company_name}"

    class Meta:
        ordering = ['cena_po_nocenju']
        verbose_name = 'Smestaj'
        verbose_name_plural = 'Smestaji'


class SmestajReservation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    smestaj = models.ForeignKey(
        Smestaj,
        on_delete=models.CASCADE,
        related_name='rezervacije'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='smestaj_rezervacije'
    )
    check_in = models.DateField()
    check_out = models.DateField()
    broj_odraslih = models.IntegerField(default=1)
    broj_dece = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    napomena = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    revenue_updated = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.smestaj.naziv} ({self.check_in} → {self.check_out})"
    
    def calculate_total_price(self):
        """Calculate total price based on nights and price per night"""
        nights = (self.check_out - self.check_in).days
        return nights * self.smestaj.cena_po_nocenju
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.calculate_total_price()
        super().save(*args, **kwargs)
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    smestaj = models.ForeignKey(
        Smestaj,
        on_delete=models.CASCADE,
        related_name='rezervacije'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='smestaj_rezervacije'
    )
    check_in = models.DateField()
    check_out = models.DateField()
    broj_odraslih = models.IntegerField(default=1)
    broj_dece = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    napomena = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.smestaj.naziv} ({self.check_in} → {self.check_out})"