from django.contrib import admin
from .models import *


@admin.register(ParentRegisteration)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "credits", "created_at")
    readonly_fields = ("created_at",)


@admin.register(PrimaryStudentsRegister)
class PrimaryStudentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "class_year", "school", "created_at")
    readonly_fields = ("created_at",)


@admin.register(StaffRegisteration)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "credits", "created_at")
    readonly_fields = ("created_at",)


@admin.register(SecondaryStudent)
class SecondaryStudentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "class_year", "credits", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_type", "user_name", "status", "total_price", "created_at")
    readonly_fields = ("created_at",)


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
admin.site.register(OrderItem)


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ("platform", "latest_version", "min_supported_version", "force_update")
    list_editable = ("latest_version", "min_supported_version", "force_update")
