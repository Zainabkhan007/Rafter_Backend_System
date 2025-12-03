import uuid
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import JSONField
from django.contrib.auth.hashers import make_password


# ------------------------------
# School Models
# ------------------------------
class PrimarySchool(models.Model):
    school_name = models.CharField(max_length=30)
    school_email = models.EmailField(max_length=254, unique=True)
    school_eircode = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return f"{self.school_name} {self.id}"


class SecondarySchool(models.Model):
    secondary_school_name = models.CharField(max_length=30)
    secondary_school_email = models.EmailField(max_length=254, unique=True)
    secondary_school_eircode = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return f"{self.secondary_school_name}-{self.id}"


class Allergens(models.Model):
    allergy = models.CharField(max_length=50)


# ------------------------------
# User Models
# ------------------------------
class ParentRegisteration(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=30, blank=True, null=True) 
    email = models.EmailField(max_length=254, unique=True)
    phone_no = models.BigIntegerField(blank=True, null=True)
    password = models.CharField(max_length=128)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    allergies = models.ManyToManyField(Allergens, blank=True)
    credits = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        if self.password and (not self.pk or not ParentRegisteration.objects.filter(id=self.pk, password=self.password).exists()):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def top_up_credits(self, amount):
        self.credits += amount
        self.save()


class StaffRegisteration(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True)
    phone_no = models.BigIntegerField(blank=True, null=True)
    allergies = models.ManyToManyField(Allergens, blank=True)
    password = models.CharField(max_length=128)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    primary_school = models.ForeignKey(PrimarySchool, on_delete=models.CASCADE, null=True, blank=True)
    secondary_school = models.ForeignKey(SecondarySchool, on_delete=models.CASCADE, null=True, blank=True)
    credits = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        if self.password and (not self.pk or not StaffRegisteration.objects.filter(id=self.pk, password=self.password).exists()):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def top_up_credits(self, amount):
        self.credits += amount
        self.save()

    def __str__(self):
        return f"{self.id}"


def get_expiry_time():
    return timezone.now() + timedelta(hours=1)


class UnverifiedUser(models.Model):
    email = models.EmailField()
    data = models.JSONField()
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField(default=get_expiry_time)
    login_method = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('google', 'Google'), ('facebook', 'Facebook'), ('microsoft', 'Microsoft')],
        default='email'
    )


class Teacher(models.Model):
    teacher_name = models.CharField(max_length=30)
    class_year = models.CharField(max_length=30)
    school = models.ForeignKey(PrimarySchool, on_delete=models.CASCADE, related_name='teachers')

    def __str__(self):
        return f"{self.teacher_name} - {self.class_year} {self.id}"


class SecondaryStudent(models.Model):
    first_name = models.CharField(max_length=30, default="")
    last_name = models.CharField(max_length=30, default="")
    username = models.CharField(max_length=30, default="")  
    email = models.EmailField(max_length=254, default="")
    phone_no = models.BigIntegerField(blank=True, null=True)
    password = models.CharField(max_length=128, default="")
    class_year = models.CharField(max_length=30, default="")
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    allergies = models.ManyToManyField(Allergens, blank=True)
    school = models.ForeignKey(SecondarySchool, on_delete=models.CASCADE, related_name='student', null=True, blank=True)
    credits = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        if self.password and (not self.pk or not SecondaryStudent.objects.filter(id=self.pk, password=self.password).exists()):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def top_up_credits(self, amount):
        self.credits += amount
        self.save()

    def __str__(self):
        return f"{self.username} - {self.class_year}-{self.id}"


class PrimaryStudentsRegister(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=60, blank=True, null=True) 
    class_year = models.CharField(max_length=30)
    school = models.ForeignKey(PrimarySchool, on_delete=models.CASCADE, related_name='student')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='student_teacher', null=True, blank=True)
    allergies = models.ManyToManyField(Allergens, blank=True)
    parent = models.ForeignKey(ParentRegisteration, on_delete=models.CASCADE, related_name='student_parent', null=True, blank=True)
    staff = models.ForeignKey(StaffRegisteration, on_delete=models.CASCADE, related_name='student_staff', null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} - {self.id}"


# ------------------------------
# Menu Models
# ------------------------------
class Categories(models.Model):
    name_category = models.CharField(max_length=30)
    emoji = models.ImageField(upload_to='categories_images/', blank=True, null=True)
    image = models.ImageField(upload_to='categories_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.id} - {self.name_category}"


class Menu(models.Model):
    price = models.DecimalField(max_digits=5, decimal_places=2)
    name = models.CharField(max_length=255)
    menu_day = models.CharField(max_length=100, blank=True, null=True)
    menu_date = models.DateField(default=datetime.today)
    cycle_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False) 
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name="menus")
    primary_schools = models.ManyToManyField(PrimarySchool, blank=True, related_name="menus")
    secondary_schools = models.ManyToManyField(SecondarySchool, blank=True, related_name="menus")

    def __str__(self):
        return f"{self.id} Menu: {self.menu_day} {self.name} - {self.cycle_name}"

    def delete(self, *args, **kwargs):
        # Soft delete instead of hard delete
        self.is_deleted = True
        self.save()


class MenuItems(models.Model):
    category = models.ForeignKey(
        Categories, blank=True, null=True, on_delete=models.CASCADE, related_name='menuitems'
    )
    item_name = models.CharField(max_length=255)
    item_description = models.CharField(max_length=255)
    nutrients = JSONField(default=list)
    ingredients = models.TextField(blank=True, null=True)
    allergies = models.ManyToManyField(Allergens, blank=True, related_name='menuitems')
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    
    # New fields
    production_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id} Items: {self.item_name}"


# ------------------------------
# Order Models
# ------------------------------
class Order(models.Model):
    user_id = models.BigIntegerField(null=True, blank=True)
    user_type = models.CharField(max_length=50)
    child_id = models.BigIntegerField(null=True, blank=True)
    total_price = models.FloatField()
    week_number = models.BigIntegerField(null=True)
    year = models.BigIntegerField(null=True)
    order_date = models.DateTimeField(default=datetime.utcnow)
    created_at = models.DateTimeField(default=timezone.now)
    selected_day = models.CharField(max_length=10)
    is_delivered = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='pending')
    primary_student = models.ForeignKey(PrimaryStudentsRegister, null=True, blank=True, on_delete=models.CASCADE, related_name='primary_student')
    staff = models.ForeignKey(StaffRegisteration, null=True, blank=True, on_delete=models.CASCADE, related_name='staff')
    student = models.ForeignKey(SecondaryStudent, null=True, blank=True, on_delete=models.CASCADE, related_name='student')
    user_name = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    primary_school = models.ForeignKey(PrimarySchool, on_delete=models.SET_NULL, null=True, blank=True)
    secondary_school = models.ForeignKey(SecondarySchool, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.user_name = self.get_user_name()
        super().save(*args, **kwargs)

    def get_user_name(self):
        if self.user_type == 'student':
            student = SecondaryStudent.objects.filter(id=self.user_id).first()
            if student:
                return student.username
        elif self.user_type == 'parent':
            parent = ParentRegisteration.objects.filter(id=self.user_id).first()
            if parent:
                return parent.username
        elif self.user_type == 'staff':
            staff = StaffRegisteration.objects.filter(id=self.user_id).first()
            if staff:
                return staff.username
        return ""

    @property
    def order_summary(self):
        items = self.order_items.all()
        if not items:
            return "No items"
        return ", ".join([f"{item.quantity}x {item.menu_name}" for item in items])

    def __str__(self):
        return f"Order {self.id} by User {self.user_id} ({self.user_type})"


class OrderItem(models.Model):
    menu = models.ForeignKey(
        'Menu',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items_menu'
    )
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.BigIntegerField()

    # Snapshot fields
    _menu_name = models.CharField(max_length=255, blank=True, null=True)
    _menu_price = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f'OrderItem {self.id}: {self.quantity}x {self.menu_name}'

    @property
    def menu_name(self):
        # Return snapshot if exists, else current menu name
        return self._menu_name or (self.menu.name if self.menu else "Deleted Menu")

    @property
    def menu_price(self):
        return self._menu_price or (self.menu.price if self.menu else 0)


# ------------------------------
# Transaction/Payment Records
# ------------------------------
class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('credit', 'Credit'),
        ('refund', 'Refund'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('credits', 'Credits'),
    ]

    user_id = models.BigIntegerField()
    user_type = models.CharField(max_length=50)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    # User references
    parent = models.ForeignKey(ParentRegisteration, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    staff = models.ForeignKey(StaffRegisteration, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    student = models.ForeignKey(SecondaryStudent, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.id} - {self.user_type} {self.user_id} - {self.amount} ({self.payment_method})"


# ------------------------------
# Canteen Staff & Contact
# ------------------------------
class CanteenStaff(models.Model):
    username = models.CharField(max_length=30, blank=True, null=True) # removed unique
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)
    school_type = models.CharField(max_length=20, choices=[('primary', 'Primary'), ('secondary', 'Secondary')])
    primary_school = models.ForeignKey(PrimarySchool, on_delete=models.SET_NULL, null=True, blank=True)
    secondary_school = models.ForeignKey(SecondarySchool, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.password and (not self.pk or not CanteenStaff.objects.filter(id=self.pk, password=self.password).exists()):
            self.password = make_password(self.password)
        if self.school_type == 'primary':
            self.secondary_school = None
        elif self.school_type == 'secondary':
            self.primary_school = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} - {self.school_type}'

class Manager(models.Model):
    username = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=128)
    school_type = models.CharField(max_length=20, choices=[('primary', 'Primary'), ('secondary', 'Secondary')])
    primary_school = models.ForeignKey('PrimarySchool', on_delete=models.SET_NULL, null=True, blank=True)
    secondary_school = models.ForeignKey('SecondarySchool', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # ✅ Always lowercase username
        if self.username:
            self.username = self.username.lower()

        # ✅ Hash password if not already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        # ✅ Keep only relevant school
        if self.school_type == 'primary':
            self.secondary_school = None
        elif self.school_type == 'secondary':
            self.primary_school = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} - {self.school_type} Manager'

class ManagerOrder(models.Model):
    manager = models.ForeignKey('Manager', on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateField(null=True, blank=True) 
    week_number = models.PositiveIntegerField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')
    selected_day = models.CharField(max_length=20, blank=True, null=True)
    is_delivered = models.BooleanField(default=False)

    def __str__(self):
        return f"ManagerOrder {self.id} - {self.manager.username}"

    @property
    def total_production_price(self):
        total = sum(item.production_price or 0 for item in self.items.all())
        return total


class ManagerOrderItem(models.Model):
    order = models.ForeignKey('ManagerOrder', on_delete=models.CASCADE, related_name='items')
    day = models.CharField(max_length=50)
    item = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    remarks = models.TextField(blank=True, null=True)

    menu_item = models.ForeignKey(
        'MenuItems',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manager_order_items'
    )
    production_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)

    def save(self, *args, **kwargs):
        if self.menu_item and not self.production_price:
            self.production_price = self.menu_item.production_price or 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item} ({self.day}) x {self.quantity}"


class Worker(models.Model):
    username = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=128)

    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.lower()
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} - Worker'

class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class WorkerDocumentStatus(models.Model):
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
    ]
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name="document_statuses")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="worker_statuses")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread')
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('worker', 'document')

    def __str__(self):
        return f"{self.worker.username} - {self.document.title} ({self.status})"


class ContactMessage(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone = models.BigIntegerField(blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    photo_filename = models.CharField(max_length=255, blank=True, null=True)


# ------------------------------
# App Version
# ------------------------------
class AppVersion(models.Model):
    platform_choices = (("android", "Android"), ("ios", "iOS"))
    platform = models.CharField(max_length=10, choices=platform_choices)
    latest_version = models.CharField(max_length=20)
    min_supported_version = models.CharField(max_length=20, default="1.0.0")
    force_update = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.platform} - {self.latest_version}"
