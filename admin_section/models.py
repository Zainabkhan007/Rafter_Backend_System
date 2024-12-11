from django.db import models

# Create your models here.
class PrimarySchool(models.Model):
    school_name=models.CharField(max_length=30)
    school_email=models.EmailField(max_length=254)   
    school_eircode=models.CharField(max_length=30,unique=True)
    def __str__(self):
        return f"{self.school_name}" 

class Teacher(models.Model):
    teacher_name = models.CharField(max_length=30)
    class_year = models.CharField(max_length=30)
    school = models.ForeignKey(PrimarySchool, on_delete=models.CASCADE, related_name='teachers')
    def __str__(self):
        return f"{self.teacher_name} - {self.class_year}"


class Student(models.Model):
    student_name = models.CharField(max_length=30)
    class_year = models.CharField(max_length=30)
    school = models.ForeignKey(PrimarySchool, on_delete=models.CASCADE, related_name='student')
    teacher=models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='student_teacher')
    def __str__(self):
        return f"{self.student_name} - {self.class_year}"



class SecondarySchool(models.Model):
    secondary_school_name=models.CharField(max_length=30)
    secondary_school_email=models.EmailField(max_length=254)   
    secondary_school_eircode=models.CharField(max_length=30,unique=True)
    def __str__(self):
        return f"{self.secondary_school_name}"

class SecondaryStudent(models.Model):
    secondary_student_name = models.CharField(max_length=30)
    secondary_class_year = models.CharField(max_length=30)
    secondary_school = models.ForeignKey(SecondarySchool, on_delete=models.CASCADE, related_name='student')
    def __str__(self):
        return f"{self.secondary_student_name} - {self.secondary_class_year}"

