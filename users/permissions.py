from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
  def has_permission(self, request, view):
    return request.user.is_authenticated and request.user.role == 'admin'
  
  

class IsCompany(BasePermission):
  def has_permission(self, request, view):
    return request.user.is_authenticated and request.user.role == 'company'
  
class IsUser(BasePermission):
  def has_permission(self, request, view):
    return request.user.is_authenticated and request.user.role == 'user'
  
  
class isReporter(BasePermission):
  def has_permission(self, request, view):
    return request.user.is_authenticated and request.user.role == 'reporter'
    
class isReporterOrAdmin(BasePermission):
  def has_permission(self,request,view):
    return request.user.is_authenticated and request.user.role in ['reporter', 'admin']