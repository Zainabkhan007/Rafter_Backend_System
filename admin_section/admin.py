from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ParentRegisteration)
admin.site.register(PrimaryStudentsRegister)
admin.site.register(StaffRegisteration)
admin.site.register(CanteenStaff)
admin.site.register(PrimarySchool)
admin.site.register(Teacher)
admin.site.register(ContactMessage)
admin.site.register(SecondaryStudent)
admin.site.register(SecondarySchool)
admin.site.register(Categories)
admin.site.register(Allergens)
admin.site.register(MenuItems)
admin.site.register(Menu)
admin.site.register(Order)  
admin.site.register(OrderItem)
@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ("platform", "latest_version", "min_supported_version", "force_update")
    list_editable = ("latest_version", "min_supported_version", "force_update")
