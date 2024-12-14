from django.db import models
from datetime import datetime
from django.utils import timezone
# Create your models here.
class PrimarySchool(models.Model):
    school_name=models.CharField(max_length=30)
    school_email=models.EmailField(max_length=254)   
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
    secondary_school_email=models.EmailField(max_length=254)   
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
    menu_day = models.CharField(max_length=100, null=True, blank=True)  # Optional field for day
    menu_date = models.DateField(default=datetime.today)  # Default is today's date
    cycle_name = models.CharField(max_length=100)
    is_active_time = models.DateTimeField(auto_now_add=True) # Time when the menu becomes active
    start_date = models.DateField(auto_now_add=True,null=True, blank=True)  # When the menu becomes active
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
            # Check if the current date is within the range of start_date and end_date
            if self.start_date <= timezone.now().date() <= self.end_date:
                return True
        return False


    
class MenuItems(models.Model):
    item_name= models.CharField(max_length=255,null=False)
    item_description=models.CharField(max_length=255,null=False)
    nutrient_name=models.CharField(max_length=255,null=False)
    nutrient_quantity=models.IntegerField(null=False)

