from django.db import models
from django.contrib.auth import get_user_model
from users.models import CompanyProfile

# Create your models here.


User = get_user_model()

class SystemLog(models.Model):
    TYPE_CHOICES = (
      ('admin','Admin'),
      ('system','System'),
      ('user','User'),
      ('error','Error'),
      ('info','Info'),
    )
    
    type = models.CharField(max_length=20,choices=TYPE_CHOICES,default='info')
    message = models.TextField()
    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
      db_table = 'system_logs'
      ordering = ['-timestamp']
      
    def __str__(self):
      return f"{self.get_type_display()}: {self.message[:50]}"
    
class AdminActivity(models.Model):
  ACTION_CHOICES= (
    ('view_dashboard', 'View Dashboard'),
    ('approve_company', 'Approve Company'),
    ('reject_company', 'Reject Company'),
    ('view_users', 'View Users'),
    ('view_companies', 'View Companies'),
    ('delete_user', 'Delete User'),
    ('update_settings', 'Update Settings'),
    ('view_logs', 'View Logs'),
  )
  
  
  admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
  action = models.CharField(max_length=50, choices=ACTION_CHOICES)
  details = models.JSONField(default=dict, blank=True)
  timestamp = models.DateTimeField(auto_now_add=True)
  
  class Meta:
    db_table = 'admin_activities'
    ordering = ['-timestamp']
    
  def __str__(self):
    return f"{self.admin.email} - {self.get_action_display()}"