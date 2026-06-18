from django.conf import settings
from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField

from users.models import CompanyProfile


class Activity(models.Model):
    class Season(models.TextChoices):
        SUMMER = 'summer', 'Summer'
        WINTER = 'winter', 'Winter'
        ALL_YEAR = 'all_year', 'All Year'

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    season = models.CharField(max_length=10, choices=Season.choices, default=Season.ALL_YEAR)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField(null=True, blank=True)
    max_capacity = models.IntegerField(default=1)
    location = models.CharField(max_length=255, blank=True)
    image = CloudinaryField(
        'image',
        folder='infokop/activities',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Activity.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.company.company_name}"


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_reservations'
    )
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    number_of_people = models.IntegerField(default=1)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.activity.title} ({self.date})"