from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, APIView
import os
from rest_framework.generics import ListAPIView
from .serializers import *
import re
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter
from io import BytesIO
import openpyxl
from django.core.files.storage import FileSystemStorage
from datetime import datetime,timedelta
from django.http import HttpResponse,JsonResponse
from django.db.models import Count
from rest_framework.exceptions import NotFound
import calendar
import stripe

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth.hashers import make_password
from .models import *
from django.core.mail import send_mail
# from rest_framework.parsers import MultiPartParser, FormParser
# from django.db.models.functions import Now
stripe.api_key = settings.STRIPE_SECRET_KEY
ALLOWED_FILE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']

@api_view(["POST"])
def register(request):
    user_type = request.data.get('user_type')
    serializer = None

    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

   
    if StaffRegisteration.objects.filter(email=email).exists():
        return Response({"error": "Email already registered as staff."}, status=status.HTTP_400_BAD_REQUEST)
    if ParentRegisteration.objects.filter(email=email).exists():
        return Response({"error": "Email already registered as parent."}, status=status.HTTP_400_BAD_REQUEST)
    if SecondaryStudent.objects.filter(email=email).exists():
        return Response({"error": "Email already registered as student."}, status=status.HTTP_400_BAD_REQUEST)
    if CanteenStaff.objects.filter(email=email).exists():
        return Response({"error": "Email already registered as canteen."}, status=status.HTTP_400_BAD_REQUEST)

  
    school_id = None
    school_type = None
    if user_type in ['student', 'staff','canteenstaff']:
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
    
   
    if user_type in ['student', 'staff','canteenstaff'] and (not school_id or not school_type):
        return Response({"error": "School ID and school type are required for staff and student."}, status=status.HTTP_400_BAD_REQUEST)

    valid_school_types = ['primary', 'secondary']
    if school_type and school_type not in valid_school_types:
        return Response({"error": "Invalid school type provided."}, status=status.HTTP_400_BAD_REQUEST)

    school = None
    if school_type and school_id:
        if school_type == "primary":
            try:
                school = PrimarySchool.objects.get(id=school_id)
            except PrimarySchool.DoesNotExist:
                return Response({"error": "Primary school with this ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        elif school_type == "secondary":
            try:
                school = SecondarySchool.objects.get(id=school_id)
            except SecondarySchool.DoesNotExist:
                return Response({"error": "Secondary school with this ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)
    
   
    if user_type == "parent":
        serializer = ParentRegisterationSerializer(data=request.data)
    elif user_type == "student":
        if school:
            request.data['secondary_school'] = school.id  
        serializer = SecondaryStudentSerializer(data=request.data)
    elif user_type == "staff":
        if school:
            if school_type == "primary":
                request.data['primary_school'] = school.id  
            elif school_type == "secondary":
                request.data['secondary_school'] = school.id  
        serializer = StaffRegisterationSerializer(data=request.data)
    elif user_type == "canteenstaff":
        if school:
            if school_type == "primary":
                request.data['primary_school'] = school.id  
            elif school_type == "secondary":
                request.data['secondary_school'] = school.id
        serializer = CanteenStaffSerializer(data=request.data)
    else:
        return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

    password = request.data.get('password')
    password_confirmation = request.data.get('password_confirmation')

    
    if password != password_confirmation:
        return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

    allergies = request.data.get('allergies', [])
    for allergy in allergies:
        if not Allergens.objects.filter(allergy=allergy).exists():
            return Response({"error": f"Allergen '{allergy}' does not exist in the database."}, status=status.HTTP_400_BAD_REQUEST)

    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





    
@api_view(["POST"])
def login(request):

    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        user_type = serializer.validated_data['user_type'] 
       
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        request.session['user_id'] = user.id
        request.session['user_email'] = user.email
        request.session['user_type'] = user_type
 
        return Response({
            'access': access_token,
            'refresh': refresh_token,
            'user_type': user_type,
            'user_id': user.id,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'detail': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)



@api_view(['POST',])

def admin_login(request):
     username=request.data.get("username")
     password=request.data.get("password")
     if not username or not password:
        return Response({'detail': 'Both username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

     user = authenticate(username=username, password=password)

     if user is None:
        return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

     if not user.is_staff:
        return Response({'detail': 'You do not have permission to access this resource.'}, status=status.HTTP_403_FORBIDDEN)

     return Response({'detail': 'Login successful!'}, status=status.HTTP_200_OK)
@api_view(["GET"])
def get_user_info(request, user_type, id):
    if user_type == "parent":
        try:
            parent = ParentRegisteration.objects.get(id=id)
            students = PrimaryStudentsRegister.objects.filter(parent=parent)
            parent_serializer = ParentRegisterationSerializer(parent)
            student_serializer = PrimaryStudentSerializer(students, many=True)

           
            parent_data = parent_serializer.data
            parent_data.pop('password', None)

            student_data = student_serializer.data
            for student in student_data:
                student.pop('password', None)

            return Response({
                "user_type": "parent",
                "user_id": id,
                "parent": parent_data,
                "students": student_data
            }, status=status.HTTP_200_OK)

        except ParentRegisteration.DoesNotExist:
            return Response({"error": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

    elif user_type == "staff":
        try:
            staff = StaffRegisteration.objects.get(id=id)
            students = PrimaryStudentsRegister.objects.filter(staff=staff)
            staff_serializer = StaffRegisterationSerializer(staff)
            student_serializer = PrimaryStudentSerializer(students, many=True)

          
            staff_data = staff_serializer.data
            staff_data.pop('password', None)

            student_data = student_serializer.data
            for student in student_data:
                student.pop('password', None)

            return Response({
                "user_type": "staff",
                "user_id": id,
                "staff": staff_data,
                "students": student_data
            }, status=status.HTTP_200_OK)

        except StaffRegisteration.DoesNotExist:
            return Response({"error": "Staff not found."}, status=status.HTTP_404_NOT_FOUND)

    elif user_type == "student":
        try:
            student = SecondaryStudent.objects.get(id=id)
            student_serializer =SecondaryStudentSerializer(student)

       
            student_data = student_serializer.data
            student_data.pop('password', None)

            return Response({
                "user_type": "student",
                "user_id": id,
                "student": student_data
            }, status=status.HTTP_200_OK)

        except SecondaryStudent.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

    else:
        return Response({"error": "Invalid user_type."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT"])
def update_user_info(request, user_type, id):
   
    def exclude_password(data):
        if 'password' in data:
            data.pop('password')
        return data

    # Handling GET request
    if request.method == "GET":
        if user_type == "parent":
            try:
                parent = ParentRegisteration.objects.get(id=id)
                students = PrimaryStudentsRegister.objects.filter(parent=parent)
                parent_serializer = ParentRegisterationSerializer(parent)
                student_serializer = PrimaryStudentSerializer(students, many=True)
                parent_data = exclude_password(parent_serializer.data)  
                students_data = exclude_password(student_serializer.data)  
                return Response({
                    "user_type": "parent",
                    "user_id": id,
                    "parent": parent_data,
                    "students": students_data
                }, status=status.HTTP_200_OK)
            except ParentRegisteration.DoesNotExist:
                return Response({"error": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "staff":
            try:
                staff = StaffRegisteration.objects.get(id=id)
                students = PrimaryStudentsRegister.objects.filter(staff=staff)
                staff_serializer = StaffRegisterationSerializer(staff)
                student_serializer = PrimaryStudentSerializer(students, many=True)
                staff_data = exclude_password(staff_serializer.data)  
                students_data = exclude_password(student_serializer.data)  
                return Response({
                    "user_type": "staff",
                    "user_id": id,
                    "staff": staff_data,
                    "students": students_data
                }, status=status.HTTP_200_OK)
            except StaffRegisteration.DoesNotExist:
                return Response({"error": "Staff not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "student":
            try:
                student = SecondaryStudent.objects.get(id=id)
                student_serializer = SecondaryStudentSerializer(student)
                student_data = exclude_password(student_serializer.data) 
                return Response({
                    "user_type": "student",
                    "user_id": id,
                    "student": student_data
                }, status=status.HTTP_200_OK)
            except SecondaryStudent.DoesNotExist:
                return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        else:
            return Response({"error": "Invalid user_type."}, status=status.HTTP_400_BAD_REQUEST)

  
    elif request.method == "PUT":
        if user_type == "parent":
            try:
                parent = ParentRegisteration.objects.get(id=id)
                
                password = request.data.get('password', None)
                if password:
                    parent.set_password(password)  

                serializer = ParentRegisterationSerializer(parent, data=request.data, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    response_data = exclude_password(serializer.data) 
                    return Response({
                        "user_type": "parent",
                        "user_id": id,
                        "parent": response_data
                    }, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except ParentRegisteration.DoesNotExist:
                return Response({"error": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "staff":
            try:
                staff = StaffRegisteration.objects.get(id=id)
               
                password = request.data.get('password', None)
                if password:
                    staff.set_password(password)  

                serializer = StaffRegisterationSerializer(staff, data=request.data, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    response_data = exclude_password(serializer.data) 
                    return Response({
                        "user_type": "staff",
                        "user_id": id,
                        "staff": response_data
                    }, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except StaffRegisteration.DoesNotExist:
                return Response({"error": "Staff not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "student":
            try:
                student = SecondaryStudent.objects.get(id=id)
               
                password = request.data.get('password', None)
                if password:
                    student.set_password(password) 

                serializer = SecondaryStudentSerializer(student, data=request.data, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    response_data = exclude_password(serializer.data)
                    return Response({
                        "user_type": "student",
                        "user_id": id,
                        "student": response_data
                    }, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except SecondaryStudent.DoesNotExist:
                return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        else:
            return Response({"error": "Invalid user_type."}, status=status.HTTP_400_BAD_REQUEST)
        
# Canteen Staff
@csrf_exempt
@api_view(['GET',])
def get_cateenstaff(request):
   if request.method == "GET":
        staff = CanteenStaff.objects.all()
        serializer = CanteenStaffSerializer(staff,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT', 'DELETE'])
def cateenstaff_by_id(request, pk):
    try:
        staff = CanteenStaff.objects.get(pk=pk)  
    except CanteenStaff.DoesNotExist:
        raise NotFound({'error': 'Staff not found'}) 

    if request.method == 'GET':
    
        serializer = CanteenStaffSerializer(staff)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
      
        serializer = CanteenStaffSerializer(staff, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
       
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['POST'])
def add_child(request):
    school_name = request.data.get('school')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    class_year = request.data.get('class_year')
    teacher = request.data.get('teacher')
    allergies_data = request.data.get('allergies', [])
    user_id = request.data.get('user_id')
    user_type = request.data.get('user_type')

    if not school_name:
        return Response({"error": "School name is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not first_name:
        return Response({"error": "First name is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not last_name:
        return Response({"error": "Last name is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not class_year:
        return Response({"error": "Class year is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not user_id:
        return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    if not user_type:
        return Response({"error": "User type is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        school = PrimarySchool.objects.get(school_name=school_name)
    except PrimarySchool.DoesNotExist:
        return Response({"error": f"School '{school_name}' does not exist."}, status=status.HTTP_400_BAD_REQUEST)

    user = None
    if user_type == 'parent':
        try:
            user = ParentRegisteration.objects.get(id=user_id)
        except ParentRegisteration.DoesNotExist:
            return Response({"error": f"Parent with ID {user_id} does not exist."}, status=status.HTTP_400_BAD_REQUEST)
    elif user_type == 'staff':
        try:
            user = StaffRegisteration.objects.get(id=user_id)
        except StaffRegisteration.DoesNotExist:
            return Response({"error": f"Staff with ID {user_id} does not exist."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

   
    student_data = {
        'first_name': first_name,
        'last_name': last_name,
        'class_year': class_year,
        'school': school.id,  
        'allergies': allergies_data,
        'teacher': teacher
    }

    if user_type == 'parent':
        student_data['parent'] = user_id  
    elif user_type == 'staff':
        student_data['staff'] = user_id 

    
    serializer = PrimaryStudentSerializer(data=student_data)

    if serializer.is_valid():
        student = serializer.save()
        return Response({
            "message": "Child added successfully",
            "student": serializer.data,
            "user_type": user_type,
            "user_id": user_id
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['GET', 'PUT'])
def edit_child(request, child_id):
    child = get_object_or_404(PrimaryStudentsRegister, id=child_id)

    if request.method == 'GET':
      
        serializer = PrimaryStudentSerializer(child)
        return Response({'child': serializer.data}, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
      
        first_name = request.data.get('first_name', child.first_name)
        last_name = request.data.get('last_name', child.last_name)
        class_year = request.data.get('class_year', child.class_year)

        school_id = request.data.get('school', None)  
        allergies = request.data.get('allergies', [])

        
        if school_id:
            try:
               
                school = PrimarySchool.objects.get(id=school_id) 
                child.school = school
            except PrimarySchool.DoesNotExist:
                return Response({'message': 'School not found'}, status=status.HTTP_400_BAD_REQUEST)

        child.first_name = first_name
        child.last_name = last_name
        child.class_year = class_year

      
        if allergies is not None:
            child.allergies.clear() 
            for allergy in allergies:
                allergen = Allergens.objects.filter(allergy=allergy).first() 
                if allergen:
                    child.allergies.add(allergen)

        
        child.save()

        
        return Response({
            'message': 'Child details updated successfully.',
            'child': PrimaryStudentSerializer(child).data
        }, status=status.HTTP_200_OK)
# Primary School Sction
@csrf_exempt
@api_view(['POST'])
def add_primary_school(request):
    if request.method=='POST':
        serializer=PrimarySchoolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED, )
        else:
            return Response({ "error" : serializer.errors},status = status.HTTP_400_BAD_REQUEST)
        
@csrf_exempt
@api_view(['GET',])
def primary_school(request):
    if request.method == "GET":
        try:
           
            details = PrimarySchool.objects.annotate(student_count=Count('student'))
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
        serializer = PrimarySchoolSerializer(details, many=True)
    
        for school_data in serializer.data:
    
            school_data['student_count'] = school_data.get('student_count', 0)
        
        return Response(serializer.data)

@api_view(['GET', 'DELETE', 'PUT'])
def delete_primary_school(request, pk):
    try:
        school = PrimarySchool.objects.annotate(student_count=Count('student')).get(pk=pk)
    except PrimarySchool.DoesNotExist:
        return Response({"error": "PrimarySchool not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        serializer = PrimarySchoolSerializer(school, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        school.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PrimarySchoolSerializer(school)
    response_data = serializer.data
    response_data['student_count'] = school.student_count
    return Response(response_data, status=status.HTTP_200_OK)

class PrimarySearch(ListAPIView):

   queryset=PrimarySchool.objects.all()
   serializer_class=PrimarySchoolSerializer
   filter_backends=[SearchFilter]
   search_fields=['school_name','school_email']
   

# For Teacher
@api_view(['GET', 'POST'])
def add_and_get_teacher(request, school_id):
    school = get_object_or_404(PrimarySchool, pk=school_id)
    if request.method == 'GET':
        teachers = Teacher.objects.filter(school=school)
        teacher_serializer = TeacherSerializer(teachers, many=True)
        return Response(teacher_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        teacher_name = request.data.get('teacher_name')
        class_year = request.data.get('class_year')

        new_teacher = Teacher(
            teacher_name=teacher_name,
            class_year=class_year,
            school=school
        )
        new_teacher.save()

        teacher_serializer = TeacherSerializer(new_teacher)
        return Response(teacher_serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'DELETE'])
def update_delete_teacher(request, school_id, teacher_id):
    school = get_object_or_404(PrimarySchool, pk=school_id)
    teacher = get_object_or_404(Teacher, pk=teacher_id, school=school)

    if request.method == 'GET':
        teacher_serializer = TeacherSerializer(teacher)
        return Response(teacher_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        teacher_name = request.data.get('teacher_name', teacher.teacher_name)
        class_year = request.data.get('class_year', teacher.class_year)

        teacher.teacher_name = teacher_name
        teacher.class_year = class_year
        teacher.save()

        teacher_serializer = TeacherSerializer(teacher)
        return Response(teacher_serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        teacher.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def get_teachers(request):
 
    school_id = request.data.get('school_id')
    class_year = request.data.get('class_year')

    if not school_id or not class_year:
        return Response({'error': 'Both school_id and class_year are required.'}, status=status.HTTP_400_BAD_REQUEST)

   
    teachers = Teacher.objects.filter(school_id=school_id, class_year=class_year)

    if not teachers.exists():
        return Response({'error': 'No teachers found for the given school and class year.'}, status=status.HTTP_404_NOT_FOUND)

    teacher_details = []

    for teacher in teachers:
        teacher_data = {
            'id': teacher.id,
            'teacher_name': teacher.teacher_name,
            'class_year': teacher.class_year,
            'school_id': teacher.school.id,
            'school_name': teacher.school.school_name  
        }
        teacher_details.append(teacher_data)

 
    return Response({
        'message': 'Teachers retrieved successfully!',
        'teachers': teacher_details
    }, status=status.HTTP_200_OK)
# For Primary School Student
@api_view(['GET', 'POST'])
def get_student_detail(request, school_id):
  
    school = get_object_or_404(PrimarySchool, pk=school_id)
   
    if request.method == 'GET':
      
        students = PrimaryStudentsRegister.objects.filter(school=school)
        student_serializer = PrimaryStudentSerializer(students, many=True)
        return Response(student_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
     
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        class_year = request.data.get('class_year')
        teacher_id = request.data.get('teacher_id')

      
        teacher = get_object_or_404(Teacher, pk=teacher_id)

     
        new_student = PrimaryStudentsRegister(
            first_name=first_name,
            last_name=last_name,
            class_year=class_year,
            school=school,
            teacher=teacher
        )
        
      
        new_student.save()

       
        student_serializer = PrimaryStudentSerializer(new_student)
        return Response(student_serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'DELETE'])
def update_delete_student(request, school_id, student_id):
    school = get_object_or_404(PrimarySchool, pk=school_id)
    student = get_object_or_404(PrimaryStudentsRegister, pk=student_id, school=school)

    def exclude_password(data):
        if 'password' in data:
            data.pop('password')
        return data

   
    if request.method == 'GET':
        student_serializer = PrimaryStudentSerializer(student)
        student_data = exclude_password(student_serializer.data)  
        return Response(student_data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
      
        first_name = request.data.get('first_name', student.first_name)
        last_name = request.data.get('last_name', student.last_name)
        class_year = request.data.get('class_year', student.class_year)
        teacher_id = request.data.get('teacher', None)

     
        if teacher_id:
            teacher = get_object_or_404(Teacher, pk=teacher_id)
            student.teacher = teacher

        student.first_name = first_name
        student.last_name = last_name
        student.class_year = class_year

        
        password = request.data.get('password', None)
        if password:
            student.set_password(password)

       
        student.save()

        student_serializer = PrimaryStudentSerializer(student)
        student_data = exclude_password(student_serializer.data)
        return Response(student_data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)     

    elif request.method == 'DELETE':
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class StudentSearch(ListAPIView):
   queryset=PrimaryStudentsRegister.objects.all()
   serializer_class=PrimaryStudentsRegister
   filter_backends=[SearchFilter]
   search_fields=['student_name','class_year',"teacher"]


# Secondary School Section

@csrf_exempt
@api_view(['POST'])
def add_secondary_school(request):
    if request.method=='POST':
        serializer=SecondarySchoolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED, )
        else:
            return Response({ "error" : serializer.errors},status = status.HTTP_400_BAD_REQUEST)
        
@csrf_exempt
@api_view(['GET',])
def secondary_school(request):
   if request.method == "GET":
        try:
           
            details = SecondarySchool.objects.annotate(student_count=Count('student'))
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
        serializer = SecondarySchoolSerializer(details, many=True)
    
        for school_data in serializer.data:
    
            school_data['student_count'] = school_data.get('student_count', 0)
        
        return Response(serializer.data)


@api_view(['GET','DELETE','PUT'])
def delete_secondary_school(request,pk):
    try:
        school = SecondarySchool.objects.annotate(student_count=Count('student')).get(pk=pk)
    except SecondarySchool.DoesNotExist:
        return Response({"error": "SecondarySchool not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        serializer = SecondarySchoolSerializer(school, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        school.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = SecondarySchoolSerializer(school)
    response_data = serializer.data
    response_data['student_count'] = school.student_count
    return Response(response_data, status=status.HTTP_200_OK)


# For Secondary Student

@csrf_exempt
@api_view(['POST'])
def add_secondary_student(request, school_id):
    if request.method == 'POST':
        try:
            school = SecondarySchool.objects.get(pk=school_id)
        except SecondarySchool.DoesNotExist:
            return Response({"error": "Secondary school not found."}, status=status.HTTP_404_NOT_FOUND)

        request.data['secondary_school'] = school.id 
        serializer = SecondaryStudentSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def update_delete_secondary_student(request, school_id, student_id):
 
    school = get_object_or_404(SecondarySchool, pk=school_id)
    student = get_object_or_404(SecondaryStudent, pk=student_id, school=school)

   
    if request.method == 'GET':
        student_serializer = SecondaryStudentSerializer(student)
       
        student_data = student_serializer.data
        student_data.pop('password', None)  
        return Response(student_data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        student_name = request.data.get('secondary_student_name', student.secondary_student_name)
        class_year = request.data.get('secondary_class_year', student.secondary_class_year)

       
        student.secondary_student_name = student_name
        student.secondary_class_year = class_year
        student.save()

        student_serializer = SecondaryStudentSerializer(student)
        student_data = student_serializer.data
        student_data.pop('password', None)  
        return Response(student_data, status=status.HTTP_200_OK)

    
    elif request.method == 'DELETE':
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
@api_view(['GET', 'PUT', 'DELETE'])
def update_delete_secondary_student(request, school_id, student_id):
    def exclude_password(data):
        if 'password' in data:
            data.pop('password')
        return data
    school = get_object_or_404(SecondarySchool, pk=school_id)
    student = get_object_or_404(SecondaryStudent, pk=student_id, school=school)

    if request.method == 'GET':
        student_serializer = SecondaryStudentSerializer(student)
        return Response(student_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
       
        first_name = request.data.get('first_name', student.first_name) 
        last_name = request.data.get('last_name', student.last_name)      
        class_year = request.data.get('secondary_class_year', student.class_year)

        
        student.first_name = first_name
        student.last_name = last_name
        student.class_year = class_year
        student.save()

        student_serializer = SecondaryStudentSerializer(student)
        return Response(student_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
# Category
@csrf_exempt
@api_view(['GET',])
def get_category(request):
   if request.method == "GET":
        category = Categories.objects.all()
        serializer = CategoriesSerializer(category,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
#    Allergerns
@csrf_exempt
@api_view(['GET',])
def get_allergy(request):
   if request.method == "GET":
        allergy = Allergens.objects.all()
        serializer = AllergenSerializer(allergy,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
# Menu

@api_view(['POST'])
def add_menu(request):
    school_id = request.data.get('school_id')
    school_type = request.data.get('school_type')
    cycle_name = request.data.get('cycle_name')
    menu_date = datetime.now().date()  

    if not cycle_name.isalnum() and " " not in cycle_name:
        return Response({'error': 'Cycle Name cannot contain special characters!'}, status=status.HTTP_400_BAD_REQUEST)

    if school_type == 'primary':
        try:
            school = PrimarySchool.objects.get(id=school_id)
        except PrimarySchool.DoesNotExist:
            return Response({'error': 'Primary school not found'}, status=status.HTTP_404_NOT_FOUND)
    elif school_type == 'secondary':
        try:
            school = SecondarySchool.objects.get(id=school_id)
        except SecondarySchool.DoesNotExist:
            return Response({'error': 'Secondary school not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'error': 'Invalid school type'}, status=status.HTTP_400_BAD_REQUEST)

  
    if school_type == 'primary':
        if Menu.objects.filter(primary_school=school, cycle_name=cycle_name).exists():
            return Response({'error': 'A menu with the same cycle name already exists for this school.'}, status=status.HTTP_400_BAD_REQUEST)
    elif school_type == 'secondary':
        if Menu.objects.filter(secondary_school=school, cycle_name=cycle_name).exists():
            return Response({'error': 'A menu with the same cycle name already exists for this school.'}, status=status.HTTP_400_BAD_REQUEST)

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    created_menus = []

   
    for day in days:
        
        categories = request.data.get(f'category_{day}')
        item_names = request.data.get(f'item_names_{day}')
        prices = request.data.get(f'price_{day}')

        if not isinstance(categories, list) or not isinstance(item_names, list) or not isinstance(prices, list):
            return Response({'error': f'Invalid data format for {day}. Expecting lists of categories, item names, and prices.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(categories) != len(item_names) or len(item_names) != len(prices):
            return Response({'error': f'Inconsistent data length for {day}. Categories, item names, and prices must have the same number of items.'}, status=status.HTTP_400_BAD_REQUEST)

        for category_id, menu_name, price in zip(categories, item_names, prices):
            if not category_id or not menu_name or not price:
                return Response({'error': f'Incomplete data for {day}. Ensure all fields are filled.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                price = float(price)
                if price < 0:
                    return Response({'error': f'Price for {menu_name} on {day} must be positive.'}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({'error': f'Invalid price format for {menu_name} on {day}.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                category = Categories.objects.get(id=category_id)
            except Categories.DoesNotExist:
                return Response({'error': f'Category {category_id} not found for {menu_name} on {day}.'}, status=status.HTTP_404_NOT_FOUND)

            # Create the menu item
            menu = Menu(
                name=menu_name,
                price=price,
                primary_school=school if school_type == 'primary' else None,
                secondary_school=school if school_type == 'secondary' else None,
                menu_day=day,
                cycle_name=cycle_name,
                menu_date=menu_date,
                category=category
            )
            menu.save()
            created_menus.append(MenuSerializer(menu).data)

    return Response({'message': 'Menus created successfully!', 'menus': created_menus}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def activate_cycle(request):
    if request.method == 'POST':
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
        cycle_name = request.data.get('cycle_name')
        start_datetime = request.data.get('start_datetime')  
        end_datetime = request.data.get('end_datetime')

      
        if not cycle_name.isalnum() and " " not in cycle_name:
            return Response({'error': 'Cycle Name cannot contain special characters!'}, status=status.HTTP_400_BAD_REQUEST)

      
        try:
            if start_datetime:
                start_datetime = datetime.strptime(start_datetime, '%Y-%m-%d %I:%M %p')  
            else:
                start_datetime = None  
            
            if end_datetime:
                end_datetime = datetime.strptime(end_datetime, '%Y-%m-%d %I:%M %p')  
            else:
                end_datetime = None  
        except ValueError:
            return Response({'error': 'Invalid datetime format. Use YYYY-MM-DD HH:MM AM/PM.'}, status=status.HTTP_400_BAD_REQUEST)

    
        school_model = PrimarySchool if school_type == 'primary' else SecondarySchool
        school = school_model.objects.filter(id=school_id).first()

        if not school:
            return Response({'error': f'{school_type.capitalize()} School not found'}, status=status.HTTP_404_NOT_FOUND)

        # Deactivate previous menus for the school and cycle
        Menu.objects.filter(
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None
        ).update(is_active_time=None, end_date=datetime.today().date())

        
        menus = Menu.objects.filter(
            cycle_name=cycle_name,
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None
        )

        if not menus:
            return Response({'error': f'No menus found for cycle "{cycle_name}" in the specified school.'}, status=status.HTTP_404_NOT_FOUND)

        updated_menus = []
        for menu in menus:
            
            if start_datetime:
                menu.start_date = start_datetime.date()  
            if end_datetime:
                menu.end_date = end_datetime.date()  

            menu.is_active_time = datetime.now()  
            menu.save()

        
            start_time = start_datetime.strftime('%I:%M %p') if start_datetime else None
            end_time = end_datetime.strftime('%I:%M %p') if end_datetime else None

            updated_menus.append({
                'id': menu.id,
                'name': menu.name,
                'price': str(menu.price),
                'menu_day': menu.menu_day,
                'cycle_name': menu.cycle_name,
                'start_date': str(menu.start_date) if menu.start_date else None,
                'start_time': start_time,  
                'end_date': str(menu.end_date) if menu.end_date else None,
                'end_time': end_time,  
                'is_active': menu.is_active
            })

        return Response({
            'message': f'Cycle "{cycle_name}" activated successfully!',
            'menus': updated_menus
        }, status=status.HTTP_200_OK)


#
@api_view(['POST', 'GET', 'DELETE'])
def get_complete_menu(request):
    if request.method == 'POST':
        school_id = request.data.get('school_id')  
        school_type = request.data.get('school_type')  
        cycle_name = request.data.get('cycle_name')
        start_date = request.data.get('start_date')  
        end_date = request.data.get('end_date')  

  
        if not school_id or not school_type or not cycle_name:
            return Response({'error': 'school_id, school_type, and cycle_name are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if school_type == 'primary':
            school = PrimarySchool.objects.filter(id=school_id).first() 
        elif school_type == 'secondary':
            school = SecondarySchool.objects.filter(id=school_id).first()
        else:
            return Response({'error': 'Invalid school_type. Use "primary" or "secondary".'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not school:
            return Response({'error': f'{school_type.capitalize()} school with ID {school_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        menus = Menu.objects.filter(
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None,
            cycle_name=cycle_name
        )

        if start_date and end_date:
            menus = menus.filter(start_date__lte=start_date, end_date__gte=end_date)

        if not menus.exists():
            return Response({'error': f'No menus found for cycle "{cycle_name}" in the specified school.'}, status=status.HTTP_404_NOT_FOUND)

        menu_data = {}
        for menu in menus:
            menu_data.setdefault(menu.menu_day, []).append({
                'id': menu.id,
                'name': menu.name,
                'price': menu.price,
                'category': menu.category.name_category,
                'menu_date': menu.menu_date,
                'cycle_name': menu.cycle_name,
                'is_active': menu.is_active 
            })

        return Response({'status': 'Menus retrieved successfully!', 'menus': menu_data}, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
        cycle_name = request.data.get('cycle_name')
        start_date = request.data.get('start_date')  
        end_date = request.data.get('end_date')  

        if not school_id or not school_type or not cycle_name:
            return Response({'error': 'school_id, school_type, and cycle_name are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if school_type == 'primary':
            school = PrimarySchool.objects.filter(id=school_id).first()  
        elif school_type == 'secondary':
            school = SecondarySchool.objects.filter(id=school_id).first()
        else:
            return Response({'error': 'Invalid school_type. Use "primary" or "secondary".'}, status=status.HTTP_400_BAD_REQUEST)

        if not school:
            return Response({'error': f'{school_type.capitalize()} school with ID {school_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        menus_to_delete = Menu.objects.filter(
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None,
            cycle_name=cycle_name
        )

        if start_date and end_date:
            menus_to_delete = menus_to_delete.filter(start_date__lte=start_date, end_date__gte=end_date)

        if not menus_to_delete.exists():
            return Response({'error': f'No menus found for cycle "{cycle_name}" in the specified school.'}, status=status.HTTP_404_NOT_FOUND)

        menus_to_delete.delete()

        return Response({'message': f'All menus for cycle "{cycle_name}" in school {school_id} have been deleted.'}, status=status.HTTP_204_NO_CONTENT)

    return Response({'error': 'Invalid request method.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(["POST"])
def get_active_menu(request):
    school_type = request.data.get('school_type')
    school_id = request.data.get('school_id')

    if not school_type or not school_id:
        return Response({"detail": "Both 'school_type' and 'school_id' must be provided."},
                        status=status.HTTP_400_BAD_REQUEST)

    today = timezone.now().date()  

    try:
        if school_type == 'primary':
           
            menus = Menu.objects.filter(
                primary_school_id=school_id,
                start_date__lte=today,
                end_date__gte=today
            ).select_related('category', 'primary_school')  
            
            
            subquery = Menu.objects.filter(
                primary_school_id=school_id,
                start_date__lte=today,
                end_date__gte=today
            ).values('cycle_name').distinct()

        elif school_type == 'secondary':
         
            menus = Menu.objects.filter(
                secondary_school_id=school_id,
                start_date__lte=today,
                end_date__gte=today
            ).select_related('category', 'secondary_school') 
            
           
            subquery = Menu.objects.filter(
                secondary_school_id=school_id,
                start_date__lte=today,
                end_date__gte=today
            ).values('cycle_name').distinct()

        else:
            return Response({"detail": "Invalid school type. Please provide either 'primary' or 'secondary'."},
                            status=status.HTTP_400_BAD_REQUEST)

        
        active_menus = [menu for menu in menus if menu.is_active]

        active_cycles = [
            {"cycle": cycle['cycle_name']} 
            for cycle in subquery 
            if any(menu.cycle_name == cycle['cycle_name'] for menu in active_menus)
        ]

        
        menus_data = MenuSerializer(active_menus, many=True).data

        
        weekly_menu = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": []
        }

        
        for menu in menus_data:
            day_of_week = menu.get('menu_day')
            if day_of_week in weekly_menu:
                if school_type == 'primary':
                   
                    primary_school_name = menu.get('primary_school', {}).get('name', None)
                    category_name = menu.get('category', None)
                    weekly_menu[day_of_week].append({
                        'id':menu['id'],
                        "name": menu['name'],
                        "price": menu['price'],
                        "menu_date": menu['menu_date'],
                        "cycle_name": menu['cycle_name'],
                        "category": category_name,
                        "is_active": menu['is_active'],
                        
                    })
                elif school_type == 'secondary':
                   
                    secondary_school_name = menu.get('secondary_school', {}).get('name', None)
                    category_name = menu.get('category', None)
                    weekly_menu[day_of_week].append({
                        'id':menu['id'],
                        "name": menu['name'],
                        "price": menu['price'],
                        "menu_date": menu['menu_date'],
                        "cycle_name": menu['cycle_name'],
                        "category": category_name,
                        "is_active": menu['is_active'],
                        
                    })

        return Response({
            "menus": weekly_menu,
            "cycles": active_cycles
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["GET", "PUT"])
def edit_menu(request, id):
    print(f"Received request to edit menu item with id: {id}")
    if request.method == 'GET':
        try:
            menu_item = Menu.objects.get(id=id)
        except Menu.DoesNotExist:
            return Response({'error': 'Menu item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = MenuSerializer(menu_item)
        return Response({'menu': serializer.data}, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        try:
            menu_item = Menu.objects.get(id=id)
        except Menu.DoesNotExist:
            return Response({'error': 'Menu item not found'}, status=status.HTTP_404_NOT_FOUND)

        category = request.data.get('category')
        menu_name = request.data.get('name')
        price = request.data.get('price')
        
       
        if category:
      
            try:
                category_id = int(category) 
                category_instance = Categories.objects.get(id=category_id)  
            except ValueError:
                
                category_instance = Categories.objects.filter(name_category=category).first()
                if not category_instance:
                    return Response({'error': f'Category with name "{category}" not found.'}, status=status.HTTP_404_NOT_FOUND)
            except Categories.DoesNotExist:
                return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

            menu_item.category = category_instance

        if menu_name:
            menu_item.name = menu_name
        
        if price is not None:
            menu_item.price = price

        menu_item.save()

        serializer = MenuSerializer(menu_item)
        return Response({'message': 'Menu updated successfully!', 'menu': serializer.data}, status=status.HTTP_200_OK)

@api_view(['POST'])
def get_cycle_names(request):

    school_id = request.data.get('school_id')
    school_type = request.data.get('school_type')


    if not school_id or not school_type:
        return Response({'error': 'school_id and school_type are required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if school_type not in ['primary', 'secondary']:
        return Response({'error': 'Invalid school_type. It should be "primary" or "secondary".'}, status=status.HTTP_400_BAD_REQUEST)
    
    school_model = PrimarySchool if school_type == 'primary' else SecondarySchool
    school = school_model.objects.filter(id=school_id).first()

    if not school:
        return Response({'error': f'{school_type.capitalize()} School not found'}, status=status.HTTP_404_NOT_FOUND)

    if school_type == 'primary':
        menus = Menu.objects.filter(primary_school__id=school_id).values('cycle_name').distinct()
    elif school_type == 'secondary':
        menus = Menu.objects.filter(secondary_school__id=school_id).values('cycle_name').distinct()
    if not menus:
        return Response({'message': 'No cycle names found for this school.'}, status=status.HTTP_200_OK)

    cycle_names = [menu['cycle_name'] for menu in menus]

    return Response({
        'cycle_names': cycle_names
    }, status=status.HTTP_200_OK)



@api_view(['POST'])
def download_menu_secondary(request):
    """
    Downloads the menu data for the secondary school, including student and staff orders.
    """
    school_id = request.data.get('school_id')
    school_type = request.data.get('school_type')

    if not school_id or not school_type:
        return Response({"error": "Both school_id and school_type are required."}, status=status.HTTP_400_BAD_REQUEST)

   
    if school_type == 'secondary':
        try:
            school = SecondarySchool.objects.get(id=school_id)
        except SecondarySchool.DoesNotExist:
            return Response({"error": "Secondary school not found."}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({"error": "Invalid school type for this endpoint."}, status=status.HTTP_400_BAD_REQUEST)

    current_date = datetime.now()
    current_week, current_year = current_date.isocalendar()[1], current_date.year

   
    student_orders = Order.objects.filter(
        secondary_school=school,
        week_number=current_week,
        year=current_year
    ).select_related('student')  
    staff_orders = Order.objects.filter(
        secondary_school=school,
        week_number=current_week,
        year=current_year
    ).select_related('staff')

  
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Menu'

 
    sheet.append(["Order ID", "User Name", "Total Price", "Selected Day", "Status", "Items"])

    def get_order_items(order):
        items = OrderItem.objects.filter(order=order)
        items_data = []
        for item in items:
            items_data.append(f"{item.menu.name} x {item.quantity}") 
        return ", ".join(items_data)

 
    for order in student_orders:
        order_details = {
            "id": order.id,
            "user_name": order.user_name,
            "total_price": order.total_price,
            "selected_day": order.selected_day,
            "status": order.status,
            "items": get_order_items(order)  
        }
        sheet.append([order_details['id'], 
                      order_details['user_name'], 
                      order_details['total_price'], 
                      order_details['selected_day'], 
                      order_details['status'], 
                      order_details['items']])

   
    for order in staff_orders:
        order_details = {
            "id": order.id,
            "user_name": order.user_name,
            "total_price": order.total_price,
            "selected_day": order.selected_day,
            "status": order.status,
            "items": get_order_items(order) 
        }
        sheet.append([order_details['id'], 
                      order_details['user_name'], 
                      order_details['total_price'], 
                      order_details['selected_day'], 
                      order_details['status'], 
                      order_details['items']])

    file_stream = BytesIO()
    workbook.save(file_stream)
    file_stream.seek(0)

    filename = f"{school.secondary_school_name}_Secondary_Menu_{current_year}_Week{current_week}.xlsx"

    response = HttpResponse(file_stream.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename={filename}'
    response['Content-Length'] = str(len(file_stream.getvalue()))  
    return response

@api_view(['POST'])
def download_menu_primary(request):
    """
    Downloads the menu data for the primary school, including student and staff orders.
    """
    school_id = request.data.get('school_id')
    school_type = request.data.get('school_type')

    if not school_id or not school_type:
        return Response({"error": "Both school_id and school_type are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        school = PrimarySchool.objects.get(id=school_id)
    except PrimarySchool.DoesNotExist:
        return Response({"error": "Primary school not found."}, status=status.HTTP_404_NOT_FOUND)

    current_date = datetime.now()
    current_week, current_year = current_date.isocalendar()[1], current_date.year

   
    student_orders = Order.objects.filter(
        primary_school=school,
        week_number=current_week,
        year=current_year
    ).select_related('primary_student')

    staff_orders = Order.objects.filter(
        primary_school=school,
        week_number=current_week,
        year=current_year
    ).select_related('staff')

    
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Menu'

   
    sheet.append(["Order ID", "User Name", "Total Price", "Selected Day", "Status", "Items"])

   
    def get_order_items(order):
        items = OrderItem.objects.filter(order=order)
        items_data = []
        for item in items:
            items_data.append(f"{item.menu.name} x {item.quantity}")  
        return ", ".join(items_data)

   
    for order in student_orders:
        order_details = {
            "id": order.id,
            "user_name": order.user_name,
            "total_price": order.total_price,
            "selected_day": order.selected_day,
            "status": order.status,
            "items": get_order_items(order) 
        }
        sheet.append([order_details['id'], 
                      order_details['user_name'], 
                      order_details['total_price'], 
                      order_details['selected_day'], 
                      order_details['status'], 
                      order_details['items']])

   
    for order in staff_orders:
        order_details = {
            "id": order.id,
            "user_name": order.user_name,
            "total_price": order.total_price,
            "selected_day": order.selected_day,
            "status": order.status,
            "items": get_order_items(order)  
        }
        sheet.append([order_details['id'], 
                      order_details['user_name'], 
                      order_details['total_price'], 
                      order_details['selected_day'], 
                      order_details['status'], 
                      order_details['items']])

   
    file_stream = BytesIO()
    workbook.save(file_stream)
    file_stream.seek(0)

   
    filename = f"{school.school_name}_Primary_Menu_with_Staff_{current_year}_Week{current_week}.xlsx"

  
    response = HttpResponse(file_stream.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename={filename}'
    response['Content-Length'] = str(len(file_stream.getvalue()))  
   

    return response

# Menu Items
@csrf_exempt
@api_view(['POST'])
def add_menu_item(request):
    if request.method == 'POST':
        serializer = MenuItemsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['GET',])
def get_menu_items(request):
   if request.method == "GET":
        menu_items = MenuItems.objects.all()
        serializer = MenuItemsSerializer(menu_items,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
   
@api_view(['GET', 'PUT', 'DELETE'])
def update_menu_items(request, pk):
    try:
        menu_item = MenuItems.objects.get(pk=pk)  
    except MenuItems.DoesNotExist:
        raise NotFound({'error': 'Menu item not found'}) 

    if request.method == 'GET':
    
        serializer = MenuItemsSerializer(menu_item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
      
        serializer = MenuItemsSerializer(menu_item, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
       
        menu_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View Registered Students
@csrf_exempt
@api_view(['GET'])
def view_students(request):
    search_query = request.query_params.get('search', None)

    try:
        primary_students = PrimaryStudentsRegister.objects.all()
        secondary_students = SecondaryStudent.objects.all()

        if search_query:
            primary_students = primary_students.filter(
                student_name__icontains=search_query) | primary_students.filter(
                class_year__icontains=search_query)
            secondary_students = secondary_students.filter(
                secondary_student_name__icontains=search_query) | secondary_students.filter(
                secondary_class_year__icontains=search_query)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    primary_students_serializer = PrimaryStudentSerializer(primary_students, many=True)
    primary_students_data = primary_students_serializer.data

    for student in primary_students_data:
        student['school_type'] = 'Primary'

        if student.get('parent'):
            parent = ParentRegisteration.objects.get(id=student['parent'])
            student['email'] = parent.email if parent else None
        else:
            staff = StaffRegisteration.objects.get(id=student['staff']) if student.get('staff') else None
            student['email'] = staff.email if staff else None

    secondary_students_serializer = SecondaryStudentSerializer(secondary_students, many=True)
    secondary_students_data = secondary_students_serializer.data

    for student in secondary_students_data:
        student['school_type'] = 'Secondary'

       
        if student.get('parent'):
            try:
                parent = ParentRegisteration.objects.get(id=student['parent'])
                student['email'] = parent.email if parent else student.get('email')
            except ParentRegisteration.DoesNotExist:
                pass
        elif student.get('staff'):
            try:
                staff = StaffRegisteration.objects.get(id=student['staff'])
                student['email'] = staff.email if staff else student.get('email')
            except StaffRegisteration.DoesNotExist:
                pass

    return Response({
        'primary_students': primary_students_data,
        'secondary_students': secondary_students_data
    }, status=status.HTTP_200_OK)




@api_view(['PUT', 'GET'])
def edit_student(request, student_id):
    try:
      
        student = PrimaryStudentsRegister.objects.get(id=student_id)
        school_type = 'primary'
        serializer = PrimaryStudentSerializer(student, data=request.data, partial=True)
    except PrimaryStudentsRegister.DoesNotExist:
     
        try:
            student = SecondaryStudent.objects.get(id=student_id)
            school_type = 'secondary'
            serializer = SecondaryStudentSerializer(student, data=request.data, partial=True)
        except SecondaryStudent.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    
 
    if school_type not in ['primary', 'secondary']:
        return Response({'error': 'Invalid school type or student not found'}, status=status.HTTP_404_NOT_FOUND)
    
 
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Orders

@csrf_exempt
@api_view(['POST'])
def create_order(request):
    if request.method == 'POST':
        
        user_type = request.data.get('user_type')
        user_id = request.data.get('user_id')
        selected_days = request.data.get('selected_days')
        child_id = request.data.get('child_id', None) 
        school_id = request.data.get('school_id', None)  
        school_type = request.data.get('school_type', None)
        order_items_data = request.data.get('order_items', [])  

        if not user_type or not user_id or not selected_days:
            return Response({'error': 'User type, user ID, and selected days are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not order_items_data:
            return Response({'error': 'Order items are required.'}, status=status.HTTP_400_BAD_REQUEST)

        for item in order_items_data:
            if 'item_name' not in item or 'quantity' not in item or 'price' not in item:
                return Response({'error': 'Each order item must have item_name, quantity, and price.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = None
        if user_type == 'student':
            user = SecondaryStudent.objects.filter(id=user_id).first()
        elif user_type == 'parent':
            user = ParentRegisteration.objects.filter(id=user_id).first()
        elif user_type == 'staff':
            user = StaffRegisteration.objects.filter(id=user_id).first()

        if not user:
            return Response({'error': f'{user_type.capitalize()} not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user_type == 'student' and not school_id:
            return Response({'error': 'School ID is required for students.'}, status=status.HTTP_400_BAD_REQUEST)

        if user_type == 'parent' and not school_id:
            return Response({'error': 'School ID is required for parents.'}, status=status.HTTP_400_BAD_REQUEST)

        created_orders = [] 
        
        for idx, day in enumerate(selected_days):
            menus_for_day = Menu.objects.filter(menu_day__iexact=day)

            if not menus_for_day:
                return Response({'error': f'No menus available for {day}.'}, status=status.HTTP_404_NOT_FOUND)

            order_total_price = 0
            order_items = []  

            if idx < len(order_items_data):
                item = order_items_data[idx]
                item_name = Menu.objects.filter(name__iexact=item['item_name'], menu_day__iexact=day).first()

                if not item_name:
                    return Response({'error': f'Menu item with name {item["item_name"]} not found for {day}.'}, status=status.HTTP_404_NOT_FOUND)

               
                try:
                    item_price = float(item['price'])
                except ValueError:
                    return Response({'error': f'Invalid price value for item {item["item_name"]}.'}, status=status.HTTP_400_BAD_REQUEST)

                order_data = {
                    'user_id': user.id,
                    'user_type': user_type,
                    'total_price': 0,
                    'week_number': datetime.now().isocalendar()[1],
                    'year': datetime.now().year,
                    'order_date': datetime.now(),
                    'selected_day': day,
                    'is_delivered': False,
                    'status': 'pending',
                }

                if user_type in ['parent', 'staff'] and child_id:
                    order_data['child_id'] = child_id
                if school_type == 'primary':
                    order_data['primary_school'] = school_id
                elif school_type == 'secondary':
                    order_data['secondary_school'] = school_id

                order_serializer = OrderSerializer(data=order_data)
                if not order_serializer.is_valid():
                    return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                order_instance = order_serializer.save()

                
                order_item = OrderItem.objects.create(
                    menu=item_name,
                    quantity=item['quantity'], 
                    order=order_instance
                )
                order_items.append(order_item)

             
                order_total_price += item_price * item['quantity']

               
                order_instance.total_price = order_total_price
                order_instance.save()

               
                order_details = {
                    'order_id': order_instance.id,
                    'selected_day': day,
                    'total_price': order_instance.total_price,
                    'order_date': str(order_instance.order_date),
                    'status': 'pending',
                    'week_number': order_instance.week_number,
                    'year': order_instance.year,
                    'items': [
                        {
                            'item_name': item.menu.name,
                            'price': item_price,  
                            'quantity': item.quantity
                        } for item in order_items
                    ],
                    'user_name': order_instance.user_name, 
                }

                
                if school_type == 'primary':
                    order_details['school_id'] = school_id
                    order_details['school_type'] = 'primary'
                elif school_type == 'secondary':
                    order_details['school_id'] = school_id
                    order_details['school_type'] = 'secondary'

                if order_instance.user_type in ['parent', 'staff']:
                    order_details['child_id'] = order_instance.child_id

                created_orders.append(order_details)

        return Response({
            'message': 'Orders created successfully!',
            'orders': created_orders
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def complete_order(request):

    order_id = request.data.get('order_id')

    if not order_id:
        return Response({'error': 'Order ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        
        order = Order.objects.get(id=order_id)

        order.is_delivered = True
        order.status = 'done'
        order.save()

        return Response({
            'message': 'Order completed successfully!',
            'order_id': order.id,
            'status': order.status,
            'is_delivered': order.is_delivered,
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def cancel_order(request):
    
    order_id = request.data.get('order_id')

    if not order_id:
        return Response({'error': 'Order ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        
        order = Order.objects.get(id=order_id)

        order.status = 'cancelled'
        order.is_delivered = False
        order.save()

        return Response({
            'message': 'Order cancelled successfully!',
            'order_id': order.id,
            'status': order.status,
            'is_delivered': order.is_delivered,
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['POST'])
def add_order_item(request):
    if request.method=='POST':
        serializer=OrderItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED, )
        else:
            return Response({ "error" : serializer.errors},status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_all_orders(request):
   
    orders = Order.objects.all().order_by('-order_date')

    if not orders.exists():
        return Response({'error': 'No orders found.'}, status=status.HTTP_404_NOT_FOUND)

    order_details = []

    for order in orders:
      
        order_items = OrderItem.objects.filter(order=order)
        
        items_details = [
            {
                'item_name': item.menu.name,
                'item_price': item.menu.price,  
                'quantity': item.quantity
            }
            for item in order_items
        ]

     
        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': str(order.order_date),
            'status': order.status,
            'week_number': order.week_number,
            'year': order.year,
            'items': items_details,  
            'user_name': order.user_name,
        }

     
        if order.user_type in ['parent', 'staff']:
            order_data['child_id'] = order.child_id

    
        if order.primary_school:
            order_data['school_id'] = order.primary_school.id
            order_data['school_type'] = 'primary'
        elif order.secondary_school:
            order_data['school_id'] = order.secondary_school.id
            order_data['school_type'] = 'secondary'

        
        order_details.append(order_data)


    return Response({
        'message': 'Orders retrieved successfully!',
        'orders': order_details
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_order_by_id(request, order_id):
    try:
        
        order = Order.objects.get(id=order_id)

        
        order_items = OrderItem.objects.filter(order=order)

        
        items_details = [
            {
                'item_name': item.menu.name,
                'item_price': item.menu.price, 
                'quantity': item.quantity
            }
            for item in order_items
        ]

        
        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': str(order.order_date),
            'status': order.status,
            'week_number': order.week_number,
            'year': order.year,
            'items': items_details,  
            'user_name': order.user_name,
        }

        
        if order.user_type in ['parent', 'staff']:
            order_data['child_id'] = order.child_id
      
        if order.primary_school:
            order_data['school_id'] = order.primary_school.id
            order_data['school_type'] = 'primary'
        elif order.secondary_school:
            order_data['school_id'] = order.secondary_school.id
            order_data['school_type'] = 'secondary'
        return Response({
            'message': 'Order retrieved successfully!',
            'order': order_data
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def get_orders_by_user(request):
    
    user_id = request.data.get('user_id')
    user_type = request.data.get('user_type')

   
    if not user_id or not user_type:
        return Response({'error': 'Both user_id and user_type are required.'}, status=status.HTTP_400_BAD_REQUEST)


    if user_type not in ['student', 'parent', 'staff']:
        return Response({'error': 'Invalid user_type. It should be one of ["student", "parent", "staff"].'}, status=status.HTTP_400_BAD_REQUEST)

   
    orders = Order.objects.filter(user_id=user_id, user_type=user_type).order_by('-order_date')

    if not orders.exists():
        return Response({'error': 'No orders found for the given user.'}, status=status.HTTP_404_NOT_FOUND)

    order_details = []

    for order in orders:
       
        order_items = OrderItem.objects.filter(order=order)
        
       
        items_details = [
            {
                'item_name': item.menu.name,
                'item_price': item.menu.price,  
                'quantity': item.quantity
            }
            for item in order_items
        ]

      
        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': str(order.order_date),
            'status': order.status,
            'week_number': order.week_number,
            'year': order.year,
            'items': items_details,  
            'user_name': order.user_name,
        }

  
        if order.user_type in ['parent', 'staff']:
            order_data['child_id'] = order.child_id

      
        if order.primary_school:
            order_data['school_id'] = order.primary_school.id
            order_data['school_type'] = 'primary'
        elif order.secondary_school:
            order_data['school_id'] = order.secondary_school.id
            order_data['school_type'] = 'secondary'

       
        order_details.append(order_data)

    
    return Response({
        'message': 'Orders retrieved successfully!',
        'orders': order_details
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def get_orders_by_school(request):
   
    school_id = request.data.get('school_id')
    school_type = request.data.get('school_type')

    if not school_id or not school_type:
        return Response({'error': 'Both school_id and school_type are required.'}, status=status.HTTP_400_BAD_REQUEST)

    
    if school_type not in ['primary', 'secondary']:
        return Response({'error': 'Invalid school_type. It should be either "primary" or "secondary".'}, status=status.HTTP_400_BAD_REQUEST)

  
    if school_type == 'primary':
        orders = Order.objects.filter(primary_school_id=school_id).order_by('-order_date')
    elif school_type == 'secondary':
        orders = Order.objects.filter(secondary_school_id=school_id).order_by('-order_date')

    if not orders.exists():
        return Response({'error': 'No orders found for the given school.'}, status=status.HTTP_404_NOT_FOUND)

    order_details = []

    for order in orders:
       
        order_items = OrderItem.objects.filter(order=order)
        
        
        items_details = [
            {
                'item_name': item.menu.name,
                'item_price': item.menu.price,  
                'quantity': item.quantity
            }
            for item in order_items
        ]

        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': str(order.order_date),
            'status': order.status,
            'week_number': order.week_number,
            'year': order.year,
            'items': items_details,  
            'user_name': order.user_name,
        }

     
        if order.user_type in ['parent', 'staff']:
            order_data['child_id'] = order.child_id

        if order.primary_school:
            order_data['school_id'] = order.primary_school.id
            order_data['school_type'] = 'primary'
        elif order.secondary_school:
            order_data['school_id'] = order.secondary_school.id
            order_data['school_type'] = 'secondary'

        
        order_details.append(order_data)

    
    return Response({
        'message': 'Orders retrieved successfully!',
        'orders': order_details
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def contactmessage(request):
    """
    Handles the contact form submission. It validates the form, saves the data,
    sends an email notification, and returns a success or error response.
    """
    full_name = request.data.get('full_name')
    email = request.data.get('email')
    phone = request.data.get('phone')
    subject = request.data.get('subject')
    message = request.data.get('message')
    photo = request.FILES.get('photo')  
   
    if not full_name or not email or not subject or not message:
        return Response({"error": "Full name, email, subject, and message are required."}, status=status.HTTP_400_BAD_REQUEST)

   
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return Response({"error": "Invalid email format."}, status=status.HTTP_400_BAD_REQUEST)

 
    if phone and not re.match(r'^\+?[0-9\s\-]+$', phone):
        return Response({"error": "Invalid phone number format."}, status=status.HTTP_400_BAD_REQUEST)

 
    photo_filename = None
    if photo:
        file_extension = photo.name.split('.')[-1].lower()
        if file_extension not in ALLOWED_FILE_EXTENSIONS:
            return Response({"error": "Invalid file type. Only PNG, JPG, JPEG, and GIF files are allowed."}, status=status.HTTP_400_BAD_REQUEST)

        
        if photo.size > 1024 * 1024:
            return Response({"error": "File size too large. Maximum size is 1MB."}, status=status.HTTP_400_BAD_REQUEST)

      
        fs = FileSystemStorage(location='media/contact_photos')
        
    
        photo_filename = fs.save(photo.name, photo)

  
    try:
        contact_message = ContactMessage.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            photo_filename=photo_filename if photo_filename else ""  
        )

       
        send_mail(
            subject=f"New Contact Message: {subject}",
            message=message,
            from_email=settings.MAIL_DEFAULT_SENDER,
            recipient_list=["freelancewriter3377@gmail.com"],
            fail_silently=False,
        )

        return Response({"message": "Thank you for your message! We will get back to you shortly."}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
def top_up_credits(request):
    """
    Top-up credits for the parent, staff, or student.
    """
    serializer = TopUpCreditsSerializer(data=request.data)
    
    if serializer.is_valid():
        user_id = serializer.validated_data['user_id']
        amount = serializer.validated_data['amount']
        user_type = serializer.validated_data['user_type']

      
        if user_type == "parent":
            user = ParentRegisteration.objects.filter(id=user_id).first()
        elif user_type == "staff":
            user = StaffRegisteration.objects.filter(id=user_id).first()
        elif user_type == "student":
            user = SecondaryStudent.objects.filter(id=user_id).first()

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    
        user.top_up_credits(amount)

        return Response({"message": f"{user_type.capitalize()} credits successfully updated."}, status=status.HTTP_200_OK)

    return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)



def get_current_week_and_year():
    """
    Get the current week number and year.
    """
    current_date = datetime.now()
    current_week = current_date.isocalendar()[1]  
    current_year = current_date.year
    return current_week, current_year


class CreatePaymentIntentAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
           
            data = request.data
            order_items = data.get('order_items', [])  
            total_price = float(data.get('total_price', 0)) 

           
            user_id = request.session.get('user_id')
            user_type = request.session.get('user_type')

            selected_days = data.get('selected_day', ['Monday']) 

            
            if not isinstance(selected_days, list):
                return Response({"error": "'selected_day' must be a list of days."}, status=status.HTTP_400_BAD_REQUEST)

            current_week, current_year = get_current_week_and_year()

            
            if total_price < 50:  
                return Response({"error": "Total amount must be at least ₹50."}, status=status.HTTP_400_BAD_REQUEST)

           
            payment_intent = stripe.PaymentIntent.create(
                amount=int(total_price * 100),  
                currency="inr",
                payment_method=data.get("payment_method_id"),  
                confirmation_method="manual",
                confirm=True,
                return_url=f"{request.scheme}://{request.get_host()}/payment-success/",  #
            )

           
            new_order = Order(
                user_id=user_id,
                order_date=datetime.now(),
                selected_day=", ".join(selected_days), 
                total_price=total_price,
                user_type=user_type,
                week_number=current_week,
                year=current_year,
            )
            new_order.save()

            
            for item in order_items:
                order_item = OrderItem(
                    fk_menu_item_id=item['id'],  
                    order_id=new_order.id,
                    quantity=item['quantity'],
                )
                order_item.save()

           
            return Response({
                "payment_intent": payment_intent.client_secret,  
                "order_id": new_order.id
            })

        except stripe.error.CardError as e:
            
            return Response({"error": f"Card Error: {e.user_message}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
         
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@api_view(['POST'])
def top_up_payment(request):
    """
    API to process payment for top-up credits for a parent, staff, or student.
    """
    try:
      
        user_id = request.data.get('user_id')
        amount = request.data.get('amount')
        user_type = request.data.get('user_type')
        payment_method_id = request.data.get('payment_method_id')  

        if not all([user_id, amount, user_type, payment_method_id]):
            return Response({"error": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

     
        if user_type == "parent":
            user = ParentRegisteration.objects.filter(id=user_id).first()
        elif user_type == "staff":
            user = StaffRegisteration.objects.filter(id=user_id).first()
        elif user_type == "student":
            user = SecondaryStudent.objects.filter(id=user_id).first()
        else:
            return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

       
        try:
            amount_in_cents = int(float(amount) * 100)  
        except ValueError:
            return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)

      
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_cents, 
            currency="inr",
            payment_method=payment_method_id,
            confirmation_method="manual",
            confirm=True,
        )

       
        if payment_intent.status == 'succeeded':
           
            user.top_up_credits(amount)  
            return Response({"message": f"{user_type.capitalize()} credits successfully updated."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)

    except stripe.error.CardError as e:
        return Response({"error": f"Card Error: {e.user_message}"}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.StripeError as e:
        return Response({"error": f"Stripe error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": f"Error processing payment: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)