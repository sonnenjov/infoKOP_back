from django.db import models
from users.models import User, CompanyProfile


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Na čekanju'
        CONFIRMED = 'confirmed', 'Potvrđeno'
        CANCELLED = 'cancelled', 'Otkazano'
        COMPLETED = 'completed', 'Završeno'
        CHECKEDIN = 'checkedin', 'Check-in'

    guest    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    company  = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='reservations')

    service_name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=50, blank=True)  # 'meni', 'smestaj', etc.

    date_from = models.DateField()
    date_to   = models.DateField(null=True, blank=True)
    guests    = models.PositiveIntegerField(default=1)
    notes     = models.TextField(blank=True)

    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    source     = models.CharField(max_length=50, default='InfoKOP')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    channel = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        choices=[
            ('infokop', 'InfoKOP'),
            ('direct', 'Direktno'),
            ('booking', 'Booking.com'),
            ('other', 'Ostalo'),
        ],
        default='direct'
    )
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.guest} → {self.company} | {self.service_name} | {self.status}"