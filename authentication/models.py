from django.db import models
from django.contrib.auth.hashers import make_password
# Create your models here.

class ParentRegisteration(models.Model):
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)
    username=models.CharField(max_length=30)
    email=models.EmailField(max_length=254,unique=True)
    phone_no = models.IntegerField( blank=True, null=True)
    password=models.CharField(max_length=30)
    password_confirmation=models.CharField(max_length=30)
   
class StudentRegisteration(models.Model):
    first_name=models.CharField(max_length=30 )
    last_name=models.CharField(max_length=30)
    username=models.CharField(max_length=30)
    email=models.EmailField(max_length=254,unique=True)
    phone_no = models.IntegerField( blank=True, null=True)
    password=models.CharField(max_length=30)
    password_confirmation=models.CharField(max_length=30)
  
class StaffRegisteration(models.Model):
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)
    username=models.CharField(max_length=30)
    email=models.EmailField(max_length=254,unique=True)
    phone_no = models.IntegerField( blank=True, null=True)
    password=models.CharField(max_length=30)
    password_confirmation=models.CharField(max_length=30)
<<<<<<< HEAD

=======
   
>>>>>>> 6546219430c712d1c24fe84b4807f8a739ac493e
