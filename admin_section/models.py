import uuid
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import JSONField
from django.contrib.auth.hashers import make_password


# -------------------------------
# Utility
# -------------------------------
def generate_unique_username(model, first_name, last_name, pk=None):
    """Generate unique username based on first and last name for a given model"""
    base_username = f"{first_name} {last_name}".strip()
    username = base_username
    counter = 1

    while model.objects.filter(username=username).exclude(pk=pk).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    return username


# -------------------------------
# Schools
# -------------------------------
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


# -------------------------------
# Allergens
# -------------------------------
class Allergens(models.Model):
    allergy = models.CharField(max_length=50)

    def __str__(self):
        return self.allergy


# -------------------------------
# Parent
# -------------------------------
class ParentRegisteration(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=60, unique=True, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True)
    phone_no = models.BigIntegerField(blank=True, null=True)
    password = models.CharField(max_length=128)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    allergies = models.ManyToManyField(Allergens, blank=True)
    credits = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = generate_unique_username(
                ParentRegisteration, self.first_name, self.last_name, self.pk
            )
        if self.password and (
            not self.pk
            or not ParentRegisteration.objects.filter(
                id=self.pk, password=self.password
            ).exists()
        ):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def top_up_credits(self, amount):
        self.credits += amount
        self.save()

    def __str__(self):
        return self.username or f"{self.first_name} {self.last_name}"


# -------------------------------
# Staff
# -------------------------------
class StaffRegisteration(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=60, unique=True, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True)
    phone_no = models.BigIntegerField(blank=True, null=True)
    allergies = models.ManyToManyField(Allergens, blank=True)
    password = models.CharField(max_length=128)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    primary_school = models.ForeignKey(
        PrimarySchool, on_delete=models.CASCADE, null=True, blank=True
    )
    secondary_school = models.ForeignKey(
        SecondarySchool, on_delete=models.CASCADE, null=True, blank=True
    )
    credits = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = generate_unique_username(
                StaffRegisteration, self.first_name, self.last_name, self.pk
            )
        if self.password and (
            not self.pk
            or not StaffRegisteration.objects.filter(
                id=self.pk, password=self.password
            ).exists()
        ):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def top_up_credits(self, amount):
        self.credits += amount
        self.save()

    def __str__(self):
        return self.username or f"{self.first_name} {self.last_name}"


# -------------------------------
# Unverified Users
# -------------------------------
def get_expiry_time():
    return timezone.now() + timedelta(hours=1)


class UnverifiedUser(models.Model):
    email = models.EmailField()
    data = models.JSONField()
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    expiry_time = models.DateTimeField(default=get_expiry_time)
    login_method = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("google", "Google"),
            ("facebook", "Facebook"),
            ("microsoft", "Microsoft"),
        ],
        default="email",
    )


# -------------------------------
# Teacher
# -------------------------------
class Teacher(models.Model):
    teacher_name = models.CharField(max_length=30)
    class_year = models.CharField(max_length=30)
    school = models.ForeignKey(
        PrimarySchool, on_delete=models.CASCADE, related_name="teachers"
    )

    def __str__(self):
        return f"{self.teacher_name} - {self.class_year} {self.id}"


# -------------------------------
# Secondary Student
# -------------------------------
class SecondaryStudent(models.Model):
    first_name = models.CharField(max_length=30, default="")
    last_name = models.CharField(max_length=30, default="")
    username = models.CharField(max_length=60, unique=True, blank=True, null=True)
    email = models.EmailField(max_length=254, default="")
    phone_no = models.BigIntegerField(blank=True, null=True)
    password = models.CharField(max_length=128, default="")
    class_year = models.CharField(max_length=30, default="")
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    allergies = models.ManyToManyField(Allergens, blank=True)
    school = models.ForeignKey(
        SecondarySchool,
        on_delete=models.CASCADE,
        related_name="student",
        null=True,
        blank=True,
    )
    credits = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = generate_unique_username(
                SecondaryStudent, self.first_name, self.last_name, self.pk
            )
        if self.password and (
            not self.pk
            or not SecondaryStudent.objects.filter(
                id=self.pk, password=self.password
            ).exists()
        ):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def top_up_credits(self, amount):
        self.credits += amount
        self.save()

    def __str__(self):
        return self.username or f"{self.first_name} {self.last_name}"


# -------------------------------
# Primary Student
# -------------------------------
class PrimaryStudentsRegister(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=60, unique=True, blank=True, null=True)
    class_year = models.CharField(max_length=30)
    school = models.ForeignKey(
        PrimarySchool, on_delete=models.CASCADE, related_name="student"
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="student_teacher",
        null=True,
        blank=True,
    )
    allergies = models.ManyToManyField(Allergens, blank=True)
    parent = models.ForeignKey(
        ParentRegisteration,
        on_delete=models.CASCADE,
        related_name="student_parent",
        null=True,
        blank=True,
    )
    staff = models.ForeignKey(
        StaffRegisteration,
        on_delete=models.CASCADE,
        related_name="student_staff",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = generate_unique_username(
                PrimaryStudentsRegister, self.first_name, self.last_name, self.pk
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username or f"{self.first_name} {self.last_name}"


# -------------------------------
# Categories / Menu
# -------------------------------
class Categories(models.Model):
    name_category = models.CharField(max_length=30)
    emoji = models.ImageField(upload_to="categories_images/", blank=True, null=True)
    image = models.ImageField(upload_to="categories_images/", blank=True, null=True)

    def __str__(self):
        return f"{self.id} - {self.name_category}"


class Menu(models.Model):
    price = models.DecimalField(max_digits=5, decimal_places=2)
    name = models.CharField(max_length=255, null=False)
    menu_day = models.CharField(max_length=100, null=True, blank=True)
    menu_date = models.DateField(default=datetime.today)
    cycle_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    category = models.ForeignKey(
        Categories, null=False, blank=False, on_delete=models.CASCADE, related_name="menus"
    )

    primary_schools = models.ManyToManyField(
        PrimarySchool, blank=True, related_name="menus"
    )
    secondary_schools = models.ManyToManyField(
        SecondarySchool, blank=True, related_name="menus"
    )

    def __str__(self):
        return f"{self.id} Menu: {self.menu_day} {self.name} - {self.cycle_name}"


class MenuItems(models.Model):
    category = models.ForeignKey(
        "Categories", null=True, blank=True, on_delete=models.CASCADE, related_name="menuitems"
    )
    item_name = models.CharField(max_length=255, null=False)
    item_description = models.CharField(max_length=255, null=False)
    nutrients = JSONField(default=list)
    ingredients = models.TextField(null=True, blank=True)
    allergies = models.ManyToManyField(Allergens, blank=True, related_name="menuitems")
    image = models.ImageField(upload_to="menu_items/", blank=True, null=True)

    def __str__(self):
        return f"{self.id} Items: {self.item_name}"


# -------------------------------
# Orders
# -------------------------------
class OrderItem(models.Model):
    menu = models.ForeignKey("Menu", on_delete=models.CASCADE, related_name="menuitem")
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="orderitem")
    quantity = models.BigIntegerField()

    def __str__(self):
        return f"OrderItem {self.id}: {self.quantity}x {self.menu}"


class Order(models.Model):
    user_id = models.BigIntegerField(null=True, blank=True)
    user_type = models.CharField(max_length=50)
    child_id = models.BigIntegerField(null=True, blank=True)
    total_price = models.FloatField()
    week_number = models.BigIntegerField(null=True)
    year = models.BigIntegerField(null=True)
    order_date = models.DateTimeField(default=datetime.utcnow)
    selected_day = models.CharField(max_length=10)
    is_delivered = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="pending")
    primary_student = models.ForeignKey(
        PrimaryStudentsRegister, null=True, blank=True, on_delete=models.CASCADE, related_name="primary_student"
    )
    staff = models.ForeignKey(
        StaffRegisteration, null=True, blank=True, on_delete=models.CASCADE, related_name="staff"
    )
    student = models.ForeignKey(
        SecondaryStudent, null=True, blank=True, on_delete=models.CASCADE, related_name="student"
    )
    user_name = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=200, null=True, blank=True)
    items_name = models.ForeignKey(
        OrderItem, null=True, blank=True, on_delete=models.CASCADE, related_name="orderItem"
    )
    primary_school = models.ForeignKey(
        PrimarySchool, on_delete=models.SET_NULL, null=True, blank=True
    )
    secondary_school = models.ForeignKey(
        SecondarySchool, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"Order {self.id} by User {self.user_id} ({self.user_type})"

    def get_user_name(self):
        if self.user_type == "student":
            student = SecondaryStudent.objects.filter(id=self.user_id).first()
            if student:
                return f"{student.first_name} {student.last_name}".strip()
        elif self.user_type == "parent":
            parent = ParentRegisteration.objects.filter(id=self.user_id).first()
            if parent:
                return f"{parent.first_name} {parent.last_name}".strip()
        elif self.user_type == "staff":
            staff = StaffRegisteration.objects.filter(id=self.user_id).first()
            if staff:
                return f"{staff.first_name} {staff.last_name}".strip()
        return None

    def save(self, *args, **kwargs):
        self.user_name = self.get_user_name()
        super().save(*args, **kwargs)


# -------------------------------
# Canteen Staff
# -------------------------------
class CanteenStaff(models.Model):
    username = models.CharField(max_length=30)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)
    school_type = models.CharField(
        max_length=20, choices=[("primary", "Primary"), ("secondary", "Secondary")]
    )
    primary_school = models.ForeignKey(
        PrimarySchool, on_delete=models.SET_NULL, null=True, blank=True
    )
    secondary_school = models.ForeignKey(
        SecondarySchool, on_delete=models.SET_NULL, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if self.password and (
            not self.pk
            or not CanteenStaff.objects.filter(id=self.pk, password=self.password).exists()
        ):
            self.password = make_password(self.password)

        if self.school_type == "primary":
            self.secondary_school = None
        elif self.school_type == "secondary":
            self.primary_school = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.school_type}"


# -------------------------------
# Contact Messages
# -------------------------------
class ContactMessage(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone = models.BigIntegerField(blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    photo_filename = models.CharField(max_length=255, blank=True, null=True)


# -------------------------------
# App Version
# -------------------------------
class AppVersion(models.Model):
    platform_choices = (
        ("android", "Android"),
        ("ios", "iOS"),
    )

    platform = models.CharField(max_length=10, choices=platform_choices)
    latest_version = models.CharField(max_length=20)
    min_supported_version = models.CharField(max_length=20, default="1.0.0")
    force_update = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.platform} - {self.latest_version}"
