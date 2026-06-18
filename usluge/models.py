from django.db import models

# Create your models here.


# usluge/
#   models.py
#     - ServiceCategory     (Ski Rental, Bike Rental, Café Table...)
#     - Service             (specific offering by a partner)
#     - EquipmentItem       (physical item attached to a service)
#     - EquipmentVariant    (size 42, size 44 / red bike / blue bike)
  
#   rental.py
#     - RentalRecord        (FK to rezervacije.Booking + EquipmentItem)
  
#   availability.py
#     - get_available_qty()
#     - check_overdue()
  
#   admin.py              (register all models)
#   signals.py            (overdue alerts, low stock warnings)



# ugostitelji.Partner
#     ↓
# usluge.Service
#     ↓
# usluge.EquipmentItem
#     ↓
# rental.RentalRecord ←→ rezervacije.Booking
#     ↓
# users.Guest


# # ski_pasovi/models.py
# class SkiPass(models.Model):
#     guest = models.FK(users.User)
#     booking = models.FK(rezervacije.Booking)  # same booking
#     activated_at = models.DateTimeField()
#     valid_until = models.DateTimeField()
#     rfid_tag = models.CharField()             # if using physical tags
#     status = models.CharField()      


# show on specific frontend pages for user to see?8:23 PMClaude responded: Yes, exactly.Yes, exactly. That's the whole point of ServiceCategory and the partner type. Here's how it works:
# The filter chain:
# python# ugostitelji/models.py
# class Partner(models.Model):
#     name = models.CharField()
#     partner_type = models.CharField(choices=[
#         ('restaurant', 'Restaurant'),
#         ('cafe', 'Cafe'),
#         ('rental', 'Equipment Rental'),
#         ('hotel', 'Hotel'),
#         ('ski_school', 'Ski School'),
#     ])



# # usluge/models.py
# class Service(models.Model):
#     partner = models.FK(Partner)
#     category = models.FK(ServiceCategory)
#     name = models.CharField()
#     is_active = models.BooleanField()



# # Show all restaurants to user
# restaurants = Partner.objects.filter(partner_type='restaurant')

# # Show all rental stores
# rentals = Partner.objects.filter(partner_type='rental')

# # Show services of a specific partner
# services = Service.objects.filter(partner=partner, is_active=True)

# # Show only rental equipment items
# equipment = Service.objects.filter(
#     partner__partner_type='rental',
#     is_active=True
# )



# /restaurants/        → filter partner_type='restaurant'
# /cafes/              → filter partner_type='cafe'  
# /rentals/            → filter partner_type='rental'
# /rentals/<id>/       → specific store + their EquipmentItems
# /ski-school/         → filter partner_type='ski_school'




# class ServiceCategory(models.Model):
#     name = models.CharField()    # 'Coffee & Drinks'
#     slug = models.SlugField()    # 'coffee-drinks'
#     icon = models.CharField()    # for frontend display

# # Then filter by category instead of partner type
# Service.objects.filter(category__slug='coffee-drinks')