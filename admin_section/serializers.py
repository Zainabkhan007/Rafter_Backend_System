from .models import *
from rest_framework import serializers

class PrimarySchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrimarySchool
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['teacher_name', 'class_year']

class StudentSerializer(serializers.ModelSerializer):
    # Define a custom field to get the teacher's name
    teacher_name = serializers.CharField(source='teacher.teacher_name')  
    
    class Meta:
        model = Student
        fields = ['student_name', 'class_year', 'teacher_name']


class SecondarySchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecondarySchool
        fields = '__all__'


class SecondaryStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecondaryStudent
        fields = ['secondary_student_name', 'secondary_class_year','secondary_school']