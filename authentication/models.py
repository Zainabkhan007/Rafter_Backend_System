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
    password=models.CharField(max_length=30)
    password_confirmation=models.CharField(max_length=30)
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
    password=models.CharField(max_length=30)
    password_confirmation=models.CharField(max_length=30)
    def save(self, *args, **kwargs):
        # Hash the password before saving it
        if self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)