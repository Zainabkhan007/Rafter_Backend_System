from django.db import models
from datetime import datetime
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
# Create your models here.
class PrimarySchool(models.Model):
    school_name=models.CharField(max_length=30)
    school_email=models.EmailField(max_length=254,unique=True)   
    school_eircode=models.CharField(max_length=30,unique=True)
    def __str__(self):
        return f"{self.school_name}{self.id}" 

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

class Menu(models.Model):
 
    price = models.DecimalField(max_digits=5, decimal_places=2)
    name = models.CharField(max_length=255,null=False)
    menu_day = models.CharField(max_length=100, null=True, blank=True) 
    menu_date = models.DateField(default=datetime.today)  
    cycle_name = models.CharField(max_length=100)
    is_active_time = models.DateTimeField(auto_now_add=True) 
    start_date = models.DateField(auto_now_add=True,null=True, blank=True)  
    end_date = models.DateField(auto_now_add=True,null=True, blank=True) 
    # Foreign Keys
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


class MenuItems(models.Model):
    category=models.ForeignKey('Categories',null=True, blank=True,on_delete=models.CASCADE, related_name='orders')
    item_name= models.CharField(max_length=255,null=False)
    item_description=models.CharField(max_length=255,null=False)
    nutrients = JSONField(default=list)  # To store the list of nutrients as JSON
    ingredients = models.TextField(null=True, blank=True)

class Order(models.Model):
    user_id = models.IntegerField(null=True, blank=True)  
    # staff_id = models.IntegerField(null=True, blank=True)  
    user_type = models.CharField(max_length=50)  
    child_id = models.IntegerField(null=True, blank=True) 
    total_price = models.FloatField()
    week_number = models.IntegerField() 
    year = models.IntegerField() 
    order_date = models.DateTimeField(default=datetime.utcnow) 
    selected_day = models.CharField(max_length=10) 
    is_delivered = models.BooleanField(default=False)
    
    # Foreign keys for relationships
    student = models.ForeignKey('Student', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
   
    # Relationships with OrderItem
    items = models.ManyToManyField('Menu', through='OrderItem')  
    
    def __str__(self):
        return f'Order {self.id} by User {self.user_id} ({self.user_type})'


class OrderItem(models.Model):
    fk_menu_item_id = models.ForeignKey('Menu', on_delete=models.CASCADE)  # Foreign Key to Menu item
    order = models.ForeignKey('Order', on_delete=models.CASCADE)  # Foreign Key to Order
    quantity = models.IntegerField()  # How many of this item were ordered

    def __str__(self):
        return f'OrderItem {self.id}: {self.quantity}x {self.fk_menu_item_id}'
