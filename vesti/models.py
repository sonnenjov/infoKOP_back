from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
User = get_user_model()

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)


class Vest(models.Model):
    THEME_CHOICES= [
      ('sve','Sve'),
      ('infrastruktura','Infrastruktura'),
      ('vremenska prognoza','Vremenska prognoza'),
      ('sport','Sport'),
      ('aktivnosti','Aktivnosti'),
      ('dogadjaji','Dogadjaji'),
    ]
    
    
    STATUS_CHOICES = [
      ('nacrt','Nacrt'),
      ('objavljeno','Objavljeno'),
      ('zakazano','Zakazano'),
    ]
    
    
    
    PRIORITY_CHOICES = [
      ('nizak','Nizak'),
      ('srednji','Srednji'),
      ('visok','Visok'),
    ]
    
    theme = models.CharField(max_length=50, choices=THEME_CHOICES)
    title = models.CharField(max_length=200)
    image = CloudinaryField(
        'image', 
        folder='infokop/news',
        null=True,
        blank=True,
        format='webp'
    )
    text  = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,related_name='vesti')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nacrt')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='srednji')
    is_visible = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_desc = models.CharField(max_length=160, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    
    def __str__(self):
      return self.title