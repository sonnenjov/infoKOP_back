from django.conf import settings
from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from users.models import CompanyProfile


class Dogadjaj(models.Model):
    class Kategorija(models.TextChoices):
        KONCERT = 'koncerti', 'Koncerti'
        TAKMICENJE = 'takmicenja', 'Takmicenja'
        FESTIVAL = 'festivali', 'Festivali'
        EDUKACIJA = 'edukacija', 'Edukacija'

    class Season(models.TextChoices):
        SUMMER = 'summer', 'Summer'
        WINTER = 'winter', 'Winter'
        ALL_YEAR = 'all_year', 'All Year'

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='dogadjaji'
    )
    naziv = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    opis = models.TextField(blank=True)
    kategorija = models.CharField(max_length=20, choices=Kategorija.choices)
    season = models.CharField(max_length=10, choices=Season.choices, default=Season.ALL_YEAR)
    datum_pocetka = models.DateField()
    datum_zavrsetka = models.DateField(null=True, blank=True)
    vreme = models.TimeField(null=True, blank=True)
    lokacija = models.CharField(max_length=255, blank=True)
    cena = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                               help_text="Ostavite prazno za besplatne dogadjaje")
    max_kapacitet = models.IntegerField(null=True, blank=True,
                                        help_text="Ostavite prazno za neogranicen broj")
    image = CloudinaryField(
        'image',
        folder='infokop/dogadjaji',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.naziv:
            base_slug = slugify(self.naziv)
            slug = base_slug
            counter = 1
            while Dogadjaj.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.naziv} - {self.datum_pocetka} ({self.company.company_name})"

    class Meta:
        ordering = ['datum_pocetka']
        verbose_name = 'Dogadjaj'
        verbose_name_plural = 'Dogadjaji'


class DogadjajReservation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    dogadjaj = models.ForeignKey(
        Dogadjaj,
        on_delete=models.CASCADE,
        related_name='rezervacije'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dogadjaj_rezervacije'
    )
    broj_karata = models.IntegerField(default=1)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    napomena = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.dogadjaj.naziv} ({self.broj_karata} karte)"