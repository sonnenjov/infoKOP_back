from django.db import models
from users.models import CompanyProfile


class MenuCategory(models.Model):
  name = models.CharField(max_length=100)
  
  def __str__(self):
    return self.name
  
  class Meta:
    verbose_name_plural = "Menu Categories"
    
    
    
class MenuItem(models.Model):
  company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='menu_items')
  category = models.ForeignKey(MenuCategory,on_delete=models.SET_NULL, null=True, blank=True)
  name = models.CharField(max_length=200)
  description = models.TextField(blank=True)
  price = models.DecimalField(max_digits=10,decimal_places=2)
  is_available = models.BooleanField(default=True)
  allergens = models.JSONField(default=list,blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  
  
  def __str__(self):
    return f"{self.company.company_name} - {self.name}"
  
  class Meta:
    ordering = ['category', 'name']
    