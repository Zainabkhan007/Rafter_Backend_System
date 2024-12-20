from django.db import models
from datetime import datetime
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
# Create your models here.
from django.db import models
from django.contrib.auth.hashers import make_password
# Create your models here.

class ParentRegisteration(models.Model):
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)
    username=models.CharField(max_length=30)
    email=models.EmailField(max_length=254,unique=True)
    phone_no = models.IntegerField( blank=True, null=True)
    password=models.CharField(max_length=128)
    def save(self, *args, **kwargs):
        # Hash the password before saving it
        if self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
class StudentRegisteration(models.Model):
    first_name=models.CharField(max_length=30 )
    last_name=models.CharField(max_length=30)
    username=models.CharField(max_length=30)
    email=models.EmailField(max_length=254,unique=True)
    phone_no = models.IntegerField( blank=True, null=True)
    password=models.CharField(max_length=128)
    def save(self, *args, **kwargs):
        # Hash the password before saving it
        if self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class StaffRegisteration(models.Model):
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)
    username=models.CharField(max_length=30)
    email=models.EmailField(max_length=254,unique=True)
    phone_no = models.IntegerField( blank=True, null=True)
    password=models.CharField(max_length=128)
    def save(self, *args, **kwargs):
        # Hash the password before saving it
        if self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    def __str__(self):
        return f" {self.id}"



class PrimarySchool(models.Model):
    school_name=models.CharField(max_length=30)
    school_email=models.EmailField(max_length=254,unique=True)   
    school_eircode=models.CharField(max_length=30,unique=True)
    def __str__(self):
        return f"{self.school_name} {self.id}" 

class Teacher(models.Model):
    teacher_name = models.CharField(max_length=30)
    class_year = models.CharField(max_length=30)
    school = models.ForeignKey(PrimarySchool, on_delete=models.CASCADE, related_name='teachers')
    def __str__(self):
        return f"{self.teacher_name} - {self.class_year} {self.id}"


class Student(models.Model):
    student_name = models.CharField(max_length=30)
    class_year = models.CharField(max_length=30)
    student_email=models.EmailField(max_length=254,null=True, blank=True)   
    school = models.ForeignKey(PrimarySchool, on_delete=models.CASCADE, related_name='student')
    teacher=models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='student_teacher')
    def __str__(self):
        return f"{self.student_name} - {self.class_year}-{self.id}"



class SecondarySchool(models.Model):
    secondary_school_name=models.CharField(max_length=30)
    secondary_school_email=models.EmailField(max_length=254,unique=True)   
    secondary_school_eircode=models.CharField(max_length=30,unique=True)
    def __str__(self):
        return f"{self.secondary_school_name}-{self.id}"

class SecondaryStudent(models.Model):
    secondary_student_name = models.CharField(max_length=30)
    seconadry_student_email=models.EmailField(max_length=254,null=True, blank=True) 
    secondary_class_year = models.CharField(max_length=30)
    secondary_school = models.ForeignKey(SecondarySchool, on_delete=models.CASCADE, related_name='student')
    def __str__(self):
        return f"{self.secondary_student_name} - {self.secondary_class_year} {self.id}"

class Categories(models.Model):
    name_category=  models.CharField(max_length=30)
    def __str__(self):
        return f"Category: {self.name_category}"
    emoji = models.ImageField(upload_to='categories_images/', blank=True, null=True)
    image = models.ImageField(upload_to='categories_images/', blank=True, null=True)
    def __str__(self):
        return f"{self.id}"
class Menu(models.Model):
 
    price = models.DecimalField(max_digits=5, decimal_places=2)
    name = models.CharField(max_length=255,null=False)
    menu_day = models.CharField(max_length=100, null=True, blank=True) 
    menu_date = models.DateField(default=datetime.today)  
    cycle_name = models.CharField(max_length=100)
    is_active_time = models.DateTimeField(auto_now_add=True) 
    start_date = models.DateField(auto_now_add=True,null=True, blank=True)  
    end_date = models.DateField(auto_now_add=True,null=True, blank=True) 

    primary_school = models.ForeignKey(PrimarySchool, null=True, blank=True, on_delete=models.CASCADE, related_name="menus")
    secondary_school = models.ForeignKey(SecondarySchool, null=True, blank=True, on_delete=models.CASCADE, related_name="menus")
    category = models.ForeignKey(Categories, null=False, blank=False, on_delete=models.CASCADE, related_name="menus")

    def __str__(self):
        return f"{self.id} Menu:   {self.menu_day} {self.name} - {self.cycle_name}"
    @property
    def is_active(self):
        """ Returns True if the menu is active based on the start and end dates. """
        if self.start_date and self.end_date:
          
            if self.start_date <= timezone.now().date() <= self.end_date:
                return True
        return False

class Allergen(models.Model):
      allergy =  JSONField(default=list)
    
class MenuItems(models.Model):
    category=models.ForeignKey('Categories',null=True, blank=True,on_delete=models.CASCADE, related_name='menuitems')
    item_name= models.CharField(max_length=255,null=False)
    item_description=models.CharField(max_length=255,null=False)
    nutrients = JSONField(default=list)  # To store the list of nutrients as JSON
    ingredients = models.TextField(null=True, blank=True)
    allergies = models.ForeignKey(Allergen,null=True, blank=True,on_delete=models.CASCADE)  

class Order(models.Model):
    user_id = models.IntegerField(null=True, blank=True)  
   
    user_type = models.CharField(max_length=50)  
    child_id = models.IntegerField(null=True, blank=True) 
    total_price = models.FloatField()
    week_number = models.IntegerField(null=True) 
    year = models.IntegerField(null=True) 
    order_date = models.DateTimeField(default=datetime.utcnow) 
    selected_day = models.CharField(max_length=10) 
    is_delivered = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='pending')
   
    student = models.ForeignKey('Student', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    user_name = models.CharField(max_length=100, null=True, blank=True)
    
    items = models.ManyToManyField('Menu', through='OrderItem')  
    
    def __str__(self):
        return f'Order {self.id} by User {self.user_id} ({self.user_type})'

    def get_user_name(self):
        """Get the user's name based on the user type."""
        if self.user_type == 'student':
            student = StudentRegisteration.objects.filter(id=self.user_id).first()
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
        return "Unknown User"  

    def save(self, *args, **kwargs):
        """Override save method to ensure user_name is stored in the database."""
        self.user_name = self.get_user_name()  
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    menu  = models.ForeignKey('Menu', on_delete=models.CASCADE,related_name='orderitem')  
    order = models.ForeignKey('Order', on_delete=models.CASCADE,related_name='orderitem')  
    quantity = models.IntegerField() 

    def __str__(self):
        return f'OrderItem {self.id}: {self.quantity}x {self.menu }'
    

class CanteenStaff(models.Model):
    username=models.CharField(max_length=30)
    email=models.EmailField(max_length=254,unique=True)
    password=models.CharField(max_length=128)
    school_type = models.CharField(max_length=20, choices=[('primary', 'Primary'), ('secondary', 'Secondary')])
    primary_school = models.ForeignKey(PrimarySchool, on_delete=models.SET_NULL, null=True, blank=True)
    secondary_school = models.ForeignKey(SecondarySchool, on_delete=models.SET_NULL, null=True, blank=True)
    def save(self, *args, **kwargs):
        # Hash the password before saving it
        if self.password:
            self.password = make_password(self.password)

      
        if self.school_type == 'primary':
            self.secondary_school = None 
        elif self.school_type == 'secondary':
            self.primary_school = None  

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} - {self.school_type}'
class Class(models.Model):
    teacher = models.ForeignKey(StaffRegisteration, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentRegisteration, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=30)