from django.contrib import admin
from .models import *

# Register your models with their admin classes

@admin.register(ParentRegisteration)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "credits", "created_at")

@admin.register(PrimaryStudentsRegister)
class PrimaryStudentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "class_year", "school")

@admin.register(StaffRegisteration)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "credits", "created_at")

@admin.register(SecondaryStudent)
class SecondaryStudentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "class_year", "credits", "created_at")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_type", "user_name", "selected_day",
        "week_number",  "status", "total_price")

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "menu_name", "quantity", "order", "order_id") # <-- Added 'order_id' here

# Keep your simple ones as is
admin.site.register(CanteenStaff)
admin.site.register(Manager)
admin.site.register(Worker)
admin.site.register(PrimarySchool)
admin.site.register(Teacher)
admin.site.register(ContactMessage)
admin.site.register(SecondarySchool)
admin.site.register(Categories)
admin.site.register(Allergens)
admin.site.register(MenuItems)
admin.site.register(Menu)
@admin.register(ManagerOrder)
class ManagerOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'manager',
        'selected_day',
        'status',
        'is_delivered',
        'week_number',
        'year',
        'order_date',
        'total_production_price',
    )
    list_filter = ('status', 'is_delivered', 'week_number', 'year')
    search_fields = ('manager__username', 'selected_day')
    readonly_fields = ('order_date', 'total_production_price')



# ✅ ManagerOrderItem Admin (standalone view)
@admin.register(ManagerOrderItem)
class ManagerOrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'day', 'item', 'quantity', 'production_price')
    search_fields = ('item', 'day', 'order__manager__username')
    list_filter = ('day',)
    readonly_fields = ('production_price',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title", "content")
    ordering = ("-created_at",)
    list_per_page = 20


@admin.register(WorkerDocumentStatus)
class WorkerDocumentStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "worker", "document", "status", "read_at")
    list_filter = ("status", "read_at")
    search_fields = ("worker__username", "document__title")
    ordering = ("-read_at",)
    list_per_page = 30

@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ("platform", "latest_version", "min_supported_version", "force_update")
    list_editable = ("latest_version", "min_supported_version", "force_update")