from django.db import models
from django.utils import timezone
from users.models import User
class SkiPass(models.Model):
    PASS_TYPES = [
        ('daily', 'Daily'),
        ('daily3', 'Daily3'),
        ('weekly', 'Weekly'),
        ('seasonal', 'Seasonal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ski_passes')
    code = models.CharField(max_length=50, unique=True)
    pass_type = models.CharField(max_length=20, choices=PASS_TYPES)
    
    purchased_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    price_paid = models.DecimalField(max_digits=8, decimal_places=2)

    def is_valid(self):
        return not self.is_used and self.valid_until > timezone.now()

    def __str__(self):
        return f"{self.code} - {self.user.email}"