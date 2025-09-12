from django.contrib import admin
from .models import *

# Register your models with their admin classes

@admin.register(ParentRegisteration)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "credits")

@admin.register(PrimaryStudentsRegister)
class PrimaryStudentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "class_year", "school")

@admin.register(StaffRegisteration)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "credits")

@admin.register(SecondaryStudent)
class SecondaryStudentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "class_year", "credits")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_type", "user_name", "selected_day",
        "week_number",  "status", "total_price")

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "menu", "quantity", "order", "order_id") # <-- Added 'order_id' here

# Keep your simple ones as is
admin.site.register(CanteenStaff)
admin.site.register(PrimarySchool)
admin.site.register(Teacher)
admin.site.register(ContactMessage)
admin.site.register(SecondarySchool)
admin.site.register(Categories)
admin.site.register(Allergens)
admin.site.register(MenuItems)
admin.site.register(Menu)

@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ("platform", "latest_version", "min_supported_version", "force_update")
    list_editable = ("latest_version", "min_supported_version", "force_update")