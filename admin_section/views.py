from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, APIView
import os
import logging
from rest_framework.generics import ListAPIView
from .serializers import *
import re
from django.contrib.auth.models import User
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.utils.timezone import now
import logging
from collections import defaultdict
from django.utils.timezone import localtime

from io import BytesIO
from openpyxl import Workbook
from datetime import date
import datetime
import json
from django_rest_passwordreset.signals import reset_password_token_created
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
import datetime
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth.hashers import make_password
from .models import *
from django.core.mail import send_mail
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from .custom_tokens import CustomPasswordResetTokenGenerator 
logger = logging.getLogger(__name__)
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
            request.data['school'] = school.id  
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
 # Assuming this is your custom token generator

# Using your custom token generator
custom_token_generator = CustomPasswordResetTokenGenerator()

custom_token_generator = CustomPasswordResetTokenGenerator()

@api_view(["POST"])
def password_reset(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required."}, status=400)


    user = None
    try:
        user = ParentRegisteration.objects.get(email=email)
    except ParentRegisteration.DoesNotExist:
        try:
            user = StaffRegisteration.objects.get(email=email)
        except StaffRegisteration.DoesNotExist:
            try:
                user = SecondaryStudent.objects.get(email=email)
            except SecondaryStudent.DoesNotExist:
                try:
                    user = CanteenStaff.objects.get(email=email)  
                except CanteenStaff.DoesNotExist:
                    return Response({"error": "User not found."}, status=400)

   
    token = custom_token_generator.make_token(user)

    reset_link = f'https://www.raftersfoodservices.ie/password/reset/confirm/{token}/'

    send_mail(
        'Password Reset Request',
        f'Click the following link to reset your password: {reset_link}',
        'freelancewriter3377@gmail.com',
        [user.email],
        fail_silently=False,
    )

    return Response({"message": "Password reset email sent."}, status=200)




@api_view(["POST"])
def password_reset_confirm(request):
 
    token = request.data.get("token")
    password = request.data.get("password")
    email = request.data.get("email")

    if not token or not password or not email:
        return Response({"error": "Token, password, and email must be provided."}, status=400)

    try:
       
        user = None
        for model in [ParentRegisteration, StaffRegisteration, SecondaryStudent, CanteenStaff]:
            try:
                user = model.objects.get(email=email)
                break
            except model.DoesNotExist:
                continue
        
        if not user:
            return Response({"error": "User not found."}, status=400)

        
        if custom_token_generator.check_token(user, token):
            
            user.password = password 
            user.save()

            return Response({"message": "Password reset successful."}, status=200)
        else:
            return Response({"error": "Invalid token."}, status=400)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
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

            
            if student_data:
           
                school_type = "primary" if students[0].school else None
                parent_data['school_type'] = school_type
            else:
                parent_data['school_type'] = None

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

            # Adding school type to the staff response
            school_type = "primary" if staff.primary_school else "secondary" if staff.secondary_school else None
            staff_data['school_type'] = school_type

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
            student_serializer = SecondaryStudentSerializer(student)

            student_data = student_serializer.data
            student_data.pop('password', None)

            # Adding school type to the student response
            school_type = "secondary" if student.school else None
            student_data['school_type'] = school_type

            return Response({
                "user_type": "student",
                "user_id": id,
                "student": student_data
            }, status=status.HTTP_200_OK)

        except SecondaryStudent.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

    else:
        return Response({"error": "Invalid user_type."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT","DELETE"])
def update_user_info(request, user_type, id):
    # Handling GET request to fetch user data
    if request.method == "GET":
        if user_type == "parent":
            try:
                parent = ParentRegisteration.objects.get(id=id)
                parent_serializer = ParentRegisterationSerializer(parent)
                parent_data = parent_serializer.data 
                if 'password' in parent_data:
                    parent_data.pop('password') 
                return Response({
                    "user_type": "parent",
                    "user_id": id,
                    "parent": parent_data
                }, status=status.HTTP_200_OK)
            except ParentRegisteration.DoesNotExist:
                return Response({"error": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "staff":
            try:
                staff = StaffRegisteration.objects.get(id=id)
                staff_serializer = StaffRegisterationSerializer(staff)
                staff_data = staff_serializer.data 
                if 'password' in staff_data:
                    staff_data.pop('password')  
                return Response({
                    "user_type": "staff",
                    "user_id": id,
                    "staff": staff_data
                }, status=status.HTTP_200_OK)
            except StaffRegisteration.DoesNotExist:
                return Response({"error": "Staff not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "student":
            try:
                student = SecondaryStudent.objects.get(id=id)
                student_serializer = SecondaryStudentSerializer(student)
                student_data = student_serializer.data  
                if 'password' in student_data:
                    student_data.pop('password') 
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

             
                if 'password' not in request.data:
                    request.data['password'] = parent.password  

               
                serializer = ParentRegisterationSerializer(parent, data=request.data, partial=True)
                if serializer.is_valid():
                    updated_parent = serializer.save()

                
                    updated_data = serializer.data
                    if 'password' in updated_data:
                        updated_data.pop('password')

                    return Response({
                        "user_type": "parent",
                        "user_id": id,
                        "parent": updated_data,
                        "message": "Profile updated successfully."
                    }, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except ParentRegisteration.DoesNotExist:
                return Response({"error": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "staff":
            try:
                staff = StaffRegisteration.objects.get(id=id)

             
                if 'password' not in request.data:
                    request.data['password'] = staff.password 

               
                serializer = StaffRegisterationSerializer(staff, data=request.data, partial=True)
                if serializer.is_valid():
                    updated_staff = serializer.save()

                    
                    updated_data = serializer.data
                    if 'password' in updated_data:
                        updated_data.pop('password')

                    return Response({
                        "user_type": "staff",
                        "user_id": id,
                        "staff": updated_data,
                        "message": "Profile updated successfully."
                    }, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except StaffRegisteration.DoesNotExist:
                return Response({"error": "Staff not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "student":
            try:
                student = SecondaryStudent.objects.get(id=id)

              
                if 'password' not in request.data:
                    request.data['password'] = student.password 
              
                serializer = SecondaryStudentSerializer(student, data=request.data, partial=True)
                if serializer.is_valid():
                    updated_student = serializer.save()

                    
                    updated_data = serializer.data
                    if 'password' in updated_data:
                        updated_data.pop('password')

                    return Response({
                        "user_type": "student",
                        "user_id": id,
                        "student": updated_data,
                        "message": "Profile updated successfully."
                    }, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except SecondaryStudent.DoesNotExist:
                return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        else:
            return Response({"error": "Invalid user_type."}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        if user_type == "parent":
            try:
                parent = ParentRegisteration.objects.get(id=id)
                parent.delete()
                return Response({
                    "message": "Parent deleted successfully."
                }, status=status.HTTP_204_NO_CONTENT)
            except ParentRegisteration.DoesNotExist:
                return Response({"error": "Parent not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "staff":
            try:
                staff = StaffRegisteration.objects.get(id=id)
                staff.delete()
                return Response({
                    "message": "Staff deleted successfully."
                }, status=status.HTTP_204_NO_CONTENT)
            except StaffRegisteration.DoesNotExist:
                return Response({"error": "Staff not found."}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == "student":
            try:
                student = SecondaryStudent.objects.get(id=id)
                student.delete()
                return Response({
                    "message": "Student deleted successfully."
                }, status=status.HTTP_204_NO_CONTENT)
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

    # Validation checks
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

    username = f"{first_name.lower()}_{last_name.lower()}" 

    # Create student data
    student_data = {
        'first_name': first_name,
        'last_name': last_name,
        'username': username, 
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
            "user_id": user_id,
            "school_type": "primary"  
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    
@api_view(['GET', 'PUT',"DELETE"])
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
    
    elif request.method == 'DELETE':
        # Deleting the child record
        child.delete()
        return Response({
            'message': 'Child record deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)
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

@api_view(['POST'])
def add_menu(request):
    cycle_name = request.data.get('cycle_name')
    school_type = request.data.get('school_type')
    school_id = request.data.get('school_id')

    if not cycle_name:
        return Response({'error': 'Cycle name is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not school_type:
        return Response({'error': 'School type is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not school_id:
        return Response({'error': 'School ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    school = None
    try:
        if school_type == 'primary':
            school = PrimarySchool.objects.get(id=school_id)
        elif school_type == 'secondary':
            school = SecondarySchool.objects.get(id=school_id)
        else:
            return Response({'error': 'Invalid school type. Must be "primary" or "secondary"'}, status=status.HTTP_400_BAD_REQUEST)
    except PrimarySchool.DoesNotExist:
        return Response({'error': f'Primary school with ID {school_id} not found'}, status=status.HTTP_404_NOT_FOUND)
    except SecondarySchool.DoesNotExist:
        return Response({'error': f'Secondary school with ID {school_id} not found'}, status=status.HTTP_404_NOT_FOUND)

    menus = Menu.objects.filter(cycle_name=cycle_name)

    if not menus.exists():
        return Response({'error': f'No menus found for cycle name "{cycle_name}"'}, status=status.HTTP_404_NOT_FOUND)

  
    updated_menus = []
    for menu in menus:
       
        if school_type == 'primary':
            menu.primary_school = school
            menu.secondary_school = None  
        elif school_type == 'secondary':
            menu.secondary_school = school
            menu.primary_school = None  
        
        menu.save()
        updated_menus.append(MenuSerializer(menu).data)

    return Response({'message': 'Menus assigned to school successfully!', 'menus': updated_menus}, status=status.HTTP_200_OK)




@api_view(['POST'])
def activate_cycle(request):
    if request.method == 'POST':
    
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
        cycle_name = request.data.get('cycle_name')

        if not cycle_name.isalnum() and " " not in cycle_name:
            return Response({'error': 'Cycle Name cannot contain special characters!'}, status=status.HTTP_400_BAD_REQUEST)

    
        school_model = PrimarySchool if school_type == 'primary' else SecondarySchool
        school = school_model.objects.filter(id=school_id).first()


        if not school:
            return Response({'error': f'{school_type.capitalize()} School not found'}, status=status.HTTP_404_NOT_FOUND)

        Menu.objects.filter(
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None
        ).update(is_active=False)  

      
        menus = Menu.objects.filter(
            cycle_name=cycle_name,
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None
        )

        if not menus:
            return Response({'error': f'No menus found for cycle "{cycle_name}" in the specified school.'}, status=status.HTTP_404_NOT_FOUND)

        updated_menus = []
        for menu in menus:
            menu.is_active = True  
            menu.save()

            updated_menus.append({
                'id': menu.id,
                'name': menu.name,
                'price': str(menu.price),
                'menu_day': menu.menu_day,
                'cycle_name': menu.cycle_name,
                'is_active': menu.is_active
            })

      
        return Response({
            'message': f'Cycle "{cycle_name}" activated successfully!',
            'menus': updated_menus
        }, status=status.HTTP_200_OK)



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

        # Get active cycles
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
            day_of_week = menu['menu_day'] 
            if day_of_week in weekly_menu:
                
                menu_items = MenuItems.objects.filter(item_name=menu['name'])
             
                menu_items_data = []
                for item in menu_items:
                    menu_items_data.append({
                        "item_name": item.item_name,
                        "item_description": item.item_description,
                        "ingredients": item.ingredients,
                        "nutrients": item.nutrients,
                        "allergies": [allergy.allergy for allergy in item.allergies.all()]  # Correct 
                    })
                
                # Add menu and menu items data to the response structure
                if school_type == 'primary':
                    primary_school_name = menu.get('primary_school_name', None)
                    category_name = menu.get('category', None)  
                    weekly_menu[day_of_week].append({
                        'id': menu['id'],
                        "name": menu['name'],
                        "price": menu['price'],
                        "menu_date": menu['menu_date'],
                        "cycle_name": menu['cycle_name'],
                        "category": category_name,  
                        "is_active": menu['is_active'],
                        "menu_items": menu_items_data 
                    })
                elif school_type == 'secondary':
                    secondary_school_name = menu.get('secondary_school_name', None)
                    category_name = menu.get('category', None)  
                    weekly_menu[day_of_week].append({
                        'id': menu['id'],
                        "name": menu['name'],
                        "price": menu['price'],
                        "menu_date": menu['menu_date'],
                        "cycle_name": menu['cycle_name'],
                        "category": category_name, 
                        "is_active": menu['is_active'],
                        "menu_items": menu_items_data  
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



        
def get_custom_week_and_year():
    import datetime
    today = datetime.date.today()
    week_number = today.isocalendar()[1]  # Week number of the current year
    year = today.year
    return week_number, year



# MenuItems
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

        # Validate the inputs
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

        days_dict = {}
        for idx, day in enumerate(selected_days):
            if day not in days_dict:
                days_dict[day] = []
            if idx < len(order_items_data):
                days_dict[day].append(order_items_data[idx])

        for day, items_for_day in days_dict.items():
            menus_for_day = Menu.objects.filter(menu_day__iexact=day)

            if not menus_for_day:
                return Response({'error': f'No menus available for {day}.'}, status=status.HTTP_404_NOT_FOUND)

            order_total_price = 0
            order_items = []  # To store order items

            # Prepare the order data structure
            order_data = {
                'user_id': user.id,
                'user_type': user_type,
                'total_price': 0,
                'week_number': 0,  # To be calculated based on selected day
                'year': 0,
                'order_date': None,  # Set the actual order date
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

            today = datetime.today()
            target_day = day.capitalize()  # Capitalizing to match the format in Menu model
            
            # Calculate the next occurrence of the target day
            target_day_num = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(target_day)
            days_ahead = target_day_num - today.weekday()
            if days_ahead <= 0:  # If the target day is in the next week
                days_ahead += 7
            order_date = today + timedelta(days=days_ahead)

            # Calculate the week number of the target date
            week_number = order_date.isocalendar()[1]
            order_date = order_date.replace(hour=0, minute=0, second=0, microsecond=0)

            order_data['week_number'] = week_number
            order_data['year'] = order_date.year
            order_data['order_date'] = order_date

            # Create the order instance
            order_serializer = OrderSerializer(data=order_data)
            if not order_serializer.is_valid():
                return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            order_instance = order_serializer.save()

            # Assign user_name based on user_type and child_id (for parent/staff)
            if user_type == 'parent' or user_type == 'staff':
                if child_id:
                    # Fetch the child's username if child_id is provided
                    child = PrimaryStudentsRegister.objects.filter(id=child_id).first()
                    if child:
                        order_instance.user_name = child.username  # Set child username
                else:
                    
                    order_instance.user_name = None  
            else:

                order_instance.user_name = user.username

            order_instance.save()

          
            for item in items_for_day:
                item_name = item['item_name']
                item_quantity = item['quantity']

                
                menu_item = menus_for_day.filter(name__iexact=item_name).first()

                if not menu_item:
                    return Response({'error': f'Menu item {item_name} not found for {day}.'}, status=status.HTTP_404_NOT_FOUND)

              
                order_item = OrderItem.objects.create(
                    menu=menu_item,  
                    quantity=item_quantity,  
                    order=order_instance
                )

                order_items.append(order_item) 
                order_total_price += menu_item.price * item_quantity  

            
            order_instance.total_price = order_total_price
            order_instance.save()

            
            order_details = {
                'order_id': order_instance.id,
                'selected_day': day,
                'total_price': order_instance.total_price,
                'order_date': order_instance.order_date.strftime('%d %b'), 
                'status': order_instance.status,
                'week_number': order_instance.week_number,
                'year': order_instance.year,
                'items': [
                    {
                        'item_name': order_item.menu.name,
                        'price': order_item.menu.price,
                        'quantity': order_item.quantity
                    } for order_item in order_items  
                ],
                'user_name': order_instance.user_name,  
            }

            if school_type == 'primary':
                order_details['school_id'] = school_id
                order_details['school_type'] = 'primary'
            elif school_type == 'secondary':
                order_details['school_id'] = school_id
                order_details['school_type'] = 'secondary'

        
            if child_id:
                order_details['child_id'] = child_id

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

      
        credit_message = None
        user = None

        if not order.payment_method_id: 
         
            if order.user_type == 'student':
        
                user = SecondaryStudent.objects.get(id=order.user_id)
            elif order.user_type == 'parent':
            
                user = ParentRegisteration.objects.get(id=order.user_id)
            elif order.user_type == 'staff':
            
                user = StaffRegisteration.objects.get(id=order.user_id)

            user.credits += order.total_price
            user.save()

            credit_message = f"Credits of {order.total_price} have been added to your account."
        
      
        order_info = {
            'order_id': order.id,
            'user_name': order.user_name,
            'total_price': order.total_price,
            'payment_method_id': order.payment_method_id if hasattr(order, 'payment_method_id') else None,
            'status': order.status,
            'is_delivered': order.is_delivered,
            'credit_message': credit_message,
            'user_credits': user.credits if user else None, 
        }

        return Response({
            'message': 'Order cancelled successfully!',
            'order_info': order_info
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
    except (ParentRegisteration.DoesNotExist, StaffRegisteration.DoesNotExist, SecondaryStudent.DoesNotExist):
        return Response({'error': 'User not found for credits update.'}, status=status.HTTP_404_NOT_FOUND)




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
@api_view(['POST'])
def get_all_orders(request):
 
    user_type = request.data.get('user_type')
    user_id = request.data.get('user_id')
    child_id = request.data.get('child_id')

    
    if user_type == 'staff' and user_id:
        try:
            staff = StaffRegisteration.objects.get(id=user_id)
            orders = Order.objects.filter(staff=staff).order_by('-order_date')
        except StaffRegisteration.DoesNotExist:
            return Response({'error': 'Staff not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    elif user_type == 'parent' and child_id:
        try:
            child = PrimaryStudentsRegister.objects.get(id=child_id)
            orders = Order.objects.filter(child_id=child_id).order_by('-order_date')
        except PrimaryStudentsRegister.DoesNotExist:
            return Response({'error': 'Child not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    else:
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

        formatted_order_date = order.order_date.strftime('%d %b')
        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': formatted_order_date,
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

        formatted_order_date = order.order_date.strftime('%d %b')
        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': formatted_order_date,
            'status': order.status,
            'week_number': order.week_number,
            'year': order.year,
            'items': items_details,  
            'user_name': order.user_name,
            'payment_id':order.payment_id,
        }

     
        if order.user_type in ['parent', 'staff']:
            order_data['child_id'] = order.child_id

    
        if order.primary_school:
            order_data['school_id'] = order.primary_school.id
            order_data['school_name']=order.primary_school.school_name
            order_data['school_type'] = 'primary'
        elif order.secondary_school:
            order_data['school_id'] = order.secondary_school.id
            order_data['school_name']=order.secondary_school.secondary_school_name
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
          
        formatted_order_date = order.order_date.strftime('%d %b')
        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': formatted_order_date,
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
    child_id = request.data.get('child_id')  
   
    if not user_type:
        return Response({'error': 'user_type is required.'}, status=status.HTTP_400_BAD_REQUEST)


    if user_type not in ['student', 'parent', 'staff']:
        return Response({'error': 'Invalid user_type. It should be one of ["student", "parent", "staff"].'}, status=status.HTTP_400_BAD_REQUEST)

 
    orders = Order.objects.none()

    if user_type == 'staff' and child_id:
        orders = Order.objects.filter(child_id=child_id).order_by('-order_date')

    elif user_type == 'staff' and user_id:
        orders = Order.objects.filter(user_id=user_id,user_type='staff').order_by('-order_date')

   
    elif user_type == 'parent':
        orders = Order.objects.filter(user_id=user_id, user_type='parent').order_by('-order_date')

    
    elif user_type == 'student':
        orders = Order.objects.filter(user_id=user_id, user_type='student').order_by('-order_date')

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

        formatted_order_date = order.order_date.strftime('%d %b')
        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': formatted_order_date,
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




class CreateOrderAndPaymentAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            user_type = data.get('user_type')
            user_id = data.get('user_id')
            selected_days = data.get('selected_days')
            order_items_data = data.get('order_items', [])
            school_id = data.get('school_id', None)
            school_type = data.get('school_type', None)
            child_id = data.get('child_id', None)
            payment_id = data.get("payment_id", None)
            front_end_total_price = float(data.get("total_price", 0))

            if not user_type or not user_id or not selected_days:
                return Response({'error': 'User type, user ID, and selected days are required.'}, status=status.HTTP_400_BAD_REQUEST)

            if not order_items_data:
                return Response({'error': 'Order items are required.'}, status=status.HTTP_400_BAD_REQUEST)

            for item in order_items_data:
                if 'item_name' not in item or 'quantity' not in item:
                    return Response({'error': 'Each order item must have item_name and quantity.'}, status=status.HTTP_400_BAD_REQUEST)

            user = None
            if user_type == 'student':
                user = SecondaryStudent.objects.filter(id=user_id).first()
            elif user_type == 'parent':
                user = ParentRegisteration.objects.filter(id=user_id).first()
            elif user_type == 'staff':
                user = StaffRegisteration.objects.filter(id=user_id).first()

            if not user:
                return Response({'error': f'{user_type.capitalize()} not found.'}, status=status.HTTP_404_NOT_FOUND)

            if user_type in ['student', 'parent'] and not school_id:
                return Response({'error': 'School ID is required for students and parents.'}, status=status.HTTP_400_BAD_REQUEST)

            created_orders = []
            days_dict = {day: [] for day in selected_days}

            for idx, day in enumerate(selected_days):
                if idx < len(order_items_data):
                    days_dict[day].append(order_items_data[idx])

            for day, items_for_day in days_dict.items():
                menus_for_day = Menu.objects.filter(menu_day__iexact=day)

                if not menus_for_day:
                    return Response({'error': f'No menus available for {day}.'}, status=status.HTTP_404_NOT_FOUND)

                order_total_price = 0
                order_items = []

                today = datetime.today()
                target_day = day.capitalize()

                target_day_num = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(target_day)
                days_ahead = target_day_num - today.weekday()
                if days_ahead <= 0: 
                    days_ahead += 7

                order_date = today + timedelta(days=days_ahead)
                week_number = order_date.isocalendar()[1]
                order_date = order_date.replace(hour=0, minute=0, second=0, microsecond=0)

                order_data = {
                    'user_id': user.id,
                    'user_type': user_type,
                    'total_price': front_end_total_price,
                    'week_number': week_number,
                    'year': order_date.year,
                    'order_date': order_date,
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

                order_data['payment_id'] = payment_id
                order_serializer = OrderSerializer(data=order_data)
                if not order_serializer.is_valid():
                    return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                order_instance = order_serializer.save()

                for item in items_for_day:
                    menu_item = menus_for_day.filter(name__iexact=item['item_name']).first()

                    if not menu_item:
                        return Response({'error': f'Menu item with name {item["item_name"]} not found for {day}.'}, status=status.HTTP_404_NOT_FOUND)

                    item_price = float(item["price"])
                    order_item = OrderItem.objects.create(
                        menu=menu_item,
                        quantity=item['quantity'],
                        order=order_instance
                    )
                    order_items.append(order_item)
                    order_total_price += item_price * item['quantity']

                order_instance.total_price = order_total_price
                order_instance.payment_id = payment_id  
                order_instance.save()

                order_details = {
                    'order_id': order_instance.id,
                    'selected_day': day,
                    'total_price': str(order_instance.total_price),
                    'order_date': order_instance.order_date,
                    'status': 'pending',
                    'week_number': order_instance.week_number,
                    'year': order_instance.year,
                    'items': [
                        {
                            'item_name': item.menu.name,
                            'price': item.menu.price,
                            'quantity': item.quantity
                        } for item in order_items
                    ],
                    'user_name': order_instance.user_name,
                }

                created_orders.append(order_details)

        
            if not payment_id:
                if user.credits < front_end_total_price:
                    return Response({"error": "Insufficient credits to complete the order."}, status=status.HTTP_400_BAD_REQUEST)

                user.credits -= front_end_total_price  
                user.save()

              
                for order in created_orders:
                    order['status'] = 'paid'  

                return Response({
                    'message': 'Orders created and credits deducted successfully!',
                    'orders': created_orders
                }, status=status.HTTP_201_CREATED)

           
            total_price_in_cents = int(front_end_total_price * 100)
            payment_intent = stripe.PaymentIntent.create(
                amount=total_price_in_cents,
                currency="eur",
                payment_method=payment_id,
                confirmation_method="manual",
                confirm=True,
                return_url=f"{request.scheme}://{request.get_host()}/payment-success/",
            )

            for order_instance in created_orders:
                order_instance['payment_intent'] = payment_intent.client_secret

            return Response({
                'message': 'Orders and payment intent created successfully!',
                'orders': created_orders,
                'payment_intent': payment_intent.client_secret
            }, status=status.HTTP_201_CREATED)

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
            currency="eur",
            payment_method=payment_method_id,
            confirmation_method="manual",
            confirm=True,
            return_url=f"{request.scheme}://{request.get_host()}/payment-success/", 
        )

       
        if payment_intent.status == 'succeeded':
           
            user.top_up_credits(float(amount))  
            return Response({"message": f"{user_type.capitalize()} credits successfully updated."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)

    except stripe.error.CardError as e:
        return Response({"error": f"Card Error: {e.user_message}"}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.StripeError as e:
        return Response({"error": f"Stripe error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"error": f"Error processing payment: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_custom_week_and_year():
  
    today = datetime.today()
    return today.isocalendar()[1], today.year  

DAY_COLORS = {
    "Monday": "FF0000",
    "Tuesday": "00FF00",
    "Wednesday": "0000FF",
    "Thursday": "FFFF00",
    "Friday": "FF00FF",
}

CLASS_YEARS = ["1st", "2nd", "3rd", "4th", "5th", "6th"]
def fetch_orders(school_id, school_type):
    current_time = now()
    current_week_number = current_time.isocalendar()[1]
    current_year = current_time.year

    is_friday_afternoon = current_time.weekday() == 4 and current_time.hour >= 14
    target_week = current_week_number + 1 if is_friday_afternoon else current_week_number

    # Fetch orders based on school type
    orders = Order.objects.filter(
        primary_school_id=school_id if school_type == 'primary' else None,
        secondary_school_id=school_id if school_type == 'secondary' else None,
        week_number=target_week,
        year=current_year
    ).order_by('-order_date')

    student_orders = orders.exclude(user_type="staff")  # Separate student orders
    staff_orders = orders.filter(user_type="staff")  # Separate staff orders

    logger.info(f"🔍 Total {school_type} student orders: {student_orders.count()}")
    logger.info(f"👨‍🏫 Total {school_type} staff orders: {staff_orders.count()}")

    return student_orders, staff_orders
def generate_workbook(school, student_orders, staff_orders, school_type):
    workbook = Workbook()
    workbook.remove(workbook.active)

    day_totals = defaultdict(lambda: defaultdict(int))
    grouped_orders = defaultdict(lambda: defaultdict(list))
    staff_orders_by_day = defaultdict(list)  # Ensure staff orders are stored

    # Define styles
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
    center_align = Alignment(horizontal="center", vertical="center")

    def apply_styling(sheet):
        for row in sheet.iter_rows():
            for cell in row:
                cell.border = border
                cell.alignment = center_align

    # Process student orders
    for order in student_orders:
        order_items = OrderItem.objects.filter(order=order)
        selected_day = order.selected_day

        order_data = {
            'student_name': "Unknown",
            'class_year': None,
            'teacher_name': None,
            'order_items': {item.menu.name: item.quantity for item in order_items}
        }

        if school_type == 'primary':
            student = PrimaryStudentsRegister.objects.filter(id=order.child_id).first()
            if student:
                order_data['student_name'] = student.username
                order_data['teacher_name'] = student.teacher.teacher_name if student.teacher else "Unknown"

            grouped_orders[selected_day][order_data['teacher_name']].append(order_data)

        else:  # Secondary School
            student = SecondaryStudent.objects.filter(id=order.user_id).first()
            if student:
                order_data['student_name'] = student.username
                order_data['class_year'] = student.class_year if student.class_year else "Unknown"

            grouped_orders[selected_day][order_data['class_year']].append(order_data)

        for menu_name, quantity in order_data['order_items'].items():
            day_totals[selected_day][menu_name] += quantity

    # Process staff orders
    for order in staff_orders:
        order_items = OrderItem.objects.filter(order=order)
        selected_day = order.selected_day

        staff_order_data = {
            'staff_name': "Unknown",
            'order_items': {item.menu.name: item.quantity for item in order_items}
        }

        staff = StaffRegisteration.objects.filter(id=order.user_id).first()
        if staff:
            staff_order_data['staff_name'] = staff.username

        staff_orders_by_day[selected_day].append(staff_order_data)

        for menu_name, quantity in staff_order_data['order_items'].items():
            day_totals[selected_day][menu_name] += quantity

    # Create sheets for each day
    for day in DAY_COLORS.keys():
        # Add teacher/class sheets
        entity_list = Teacher.objects.filter(school=school) if school_type == 'primary' else CLASS_YEARS

        for entity in entity_list:
            entity_name = entity.teacher_name if school_type == 'primary' else entity

            sheet_title = f"{entity_name} - {day}"
            sheet = workbook.create_sheet(title=sheet_title[:31])
            sheet.sheet_properties.tabColor = DAY_COLORS.get(day, "FFFFFF")

            headers = ["Student Name", "Menu Items", "Quantity"]
            sheet.append(headers)
            for col_num, cell in enumerate(sheet[1], start=1):
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = center_align
                sheet.column_dimensions[chr(64 + col_num)].width = 20

            orders_for_entity = grouped_orders.get(day, {}).get(entity_name, [])
            for order_data in orders_for_entity:
                for menu_name, quantity in order_data['order_items'].items():
                    sheet.append([order_data['student_name'], menu_name, quantity])

            apply_styling(sheet)

        # **Always Add Staff Orders Sheet for Each Day**
        staff_sheet = workbook.create_sheet(title=f"Staff {day}")
        staff_sheet.sheet_properties.tabColor = "CCCCCC"

        staff_sheet.append(["Staff Name", "Menu Items", "Quantity"])
        for col_num, cell in enumerate(staff_sheet[1], start=1):
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_align
            staff_sheet.column_dimensions[chr(64 + col_num)].width = 20

        if day not in staff_orders_by_day or not staff_orders_by_day[day]:
            staff_sheet.append(["No orders", "", ""])  # Ensure the sheet appears
        else:
            for order_data in staff_orders_by_day[day]:
                for menu_name, quantity in order_data['order_items'].items():
                    staff_sheet.append([order_data['staff_name'], menu_name, quantity])

        apply_styling(staff_sheet)

        # **Add Day Total Sheet**
        day_total_sheet = workbook.create_sheet(title=f"{day} Total")
        day_total_sheet.sheet_properties.tabColor = "FFD700"

        day_total_sheet.append(["Menu Item", "Total Quantity"])
        for col_num, cell in enumerate(day_total_sheet[1], start=1):
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_align
            day_total_sheet.column_dimensions[chr(64 + col_num)].width = 20

        if day in day_totals:
            for menu_name, quantity in day_totals[day].items():
                day_total_sheet.append([menu_name, quantity])
        else:
            day_total_sheet.append(["No orders", ""])  # Ensure it always appears

        apply_styling(day_total_sheet)

    return workbook
@api_view(['POST'])
def download_menu(request):
    try:
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')

        logger.info(f"🔍 Received request for school_id={school_id}, school_type={school_type}")

        if not school_id or not school_type:
            return Response({'error': 'Both school_id and school_type are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if school_type not in ['primary', 'secondary']:
            return Response({'error': 'Invalid school_type. It should be either "primary" or "secondary".'}, status=status.HTTP_400_BAD_REQUEST)

        if school_type == 'primary':
            school = PrimarySchool.objects.get(id=school_id)
            logger.info(f"🏫 Primary school found: {school.school_name}")

        else:
            school = SecondarySchool.objects.get(id=school_id)
            logger.info(f"🏫 Secondary school found: {school.secondary_school_name}")

        # 🔹 Unpacking student_orders and staff_orders correctly
        student_orders, staff_orders = fetch_orders(school_id, school_type)

        # 🔹 Fix: Check if either student_orders or staff_orders is empty
        if not student_orders.exists() and not staff_orders.exists():
            logger.warning(f"⚠️ No orders found for {school_type} school ID {school_id}")
            student_orders = []  # Empty list to avoid errors
            staff_orders = []  # Empty list to avoid errors

        # 🔹 Pass both student_orders and staff_orders to generate_workbook
        workbook = generate_workbook(school, student_orders, staff_orders, school_type)

        filename = f"{school_type}_{school.secondary_school_name if school_type == 'secondary' else school.school_name}_Menu.xlsx"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        workbook.save(file_path)

        logger.info(f"✔ File generated successfully: {filename}")

        return Response({
            'message': 'File generated successfully!',
            'download_link': f"/menu_files/{filename}"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"🚨 Unexpected Error: {e}")
        return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
def get_user_count(request):
    try:
      
        parent_count = ParentRegisteration.objects.count()
        staff_count = StaffRegisteration.objects.count()
        secondary_student_count = SecondaryStudent.objects.count()
        primary_student_count = PrimaryStudentsRegister.objects.count()

    
        total_user_count = parent_count + staff_count + secondary_student_count + primary_student_count

        response_data = {
            "total_user_count": total_user_count,
           
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(["GET"])
def get_active_status_menu(request):
    today = timezone.now().date()

    primary_schools = PrimarySchool.objects.all()
    secondary_schools = SecondarySchool.objects.all()

    schools_data = []

   
    for school in primary_schools:
        menus = Menu.objects.filter(primary_school_id=school.id)

      
        weekly_menu = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": []
        }

    
        for menu in menus:
            day_of_week = menu.menu_day
            if day_of_week in weekly_menu:
                weekly_menu[day_of_week].append(menu)


        is_active = False
        active_cycle = None

        for day, day_menus in weekly_menu.items():
            if day == today.strftime("%A"): 
                for menu in day_menus:
                    if menu.is_active: 
                        active_cycle = menu.cycle_name
                        is_active = True
                        break
            if active_cycle:
                break

        
        schools_data.append({
            "school_type": "primary",
            "school_id": school.id,
            "school_name": school.school_name,
            "is_active": is_active,
            "cycle_name": active_cycle if is_active else None
        })


    for school in secondary_schools:
        menus = Menu.objects.filter(secondary_school_id=school.id)

      
        weekly_menu = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": []
        }

        for menu in menus:
            day_of_week = menu.menu_day
            if day_of_week in weekly_menu:
                weekly_menu[day_of_week].append(menu)

    
        is_active = False
        active_cycle = None

        for day, day_menus in weekly_menu.items():
            if day == today.strftime("%A"):
                for menu in day_menus:
                    if menu.is_active: 
                        active_cycle = menu.cycle_name
                        is_active = True
                        break
            if active_cycle:
                break

       
        schools_data.append({
            "school_type": "secondary",
            "school_id": school.id,
            "school_name": school.secondary_school_name,
            "is_active": is_active,
            "cycle_name": active_cycle if is_active else None  
        })

    return Response({"schools": schools_data})

@api_view(["POST"])
def deactivate_menus(request):
    try:
       
        school_type = request.data.get("school_type") 
        school_id = request.data.get("school_id")  
   
        if school_type not in ['primary', 'secondary']:
            return Response({"error": "Invalid school type. Must be 'primary' or 'secondary'."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(school_id, int) or school_id <= 0:
            return Response({"error": "Invalid school ID."}, status=status.HTTP_400_BAD_REQUEST)
        
       
        if school_type == 'primary':
            school = PrimarySchool.objects.filter(id=school_id).first()
            if not school:
                return Response({"error": "Primary school not found."}, status=status.HTTP_404_NOT_FOUND)
            menus = Menu.objects.filter(primary_school_id=school.id)
        
        elif school_type == 'secondary':
            school = SecondarySchool.objects.filter(id=school_id).first()
            if not school:
                return Response({"error": "Secondary school not found."}, status=status.HTTP_404_NOT_FOUND)
            menus = Menu.objects.filter(secondary_school_id=school.id)

       
        if not menus.exists():
            return Response({"message": "No menus found for the specified school."}, status=status.HTTP_404_NOT_FOUND)

        menus.update(is_active=False)

        return Response({"message": "All menus for the school have been deactivated successfully."}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_cycle(request):

    cycle_name = request.data.get('cycle_name')
    menu_date = datetime.now().date()  

    if not cycle_name.isalnum() and " " not in cycle_name:
        return Response({'error': 'Cycle Name cannot contain special characters!'}, status=status.HTTP_400_BAD_REQUEST)

    

  
    if Menu.objects.filter( cycle_name=cycle_name).exists():
            return Response({'error': 'A menu with the same cycle name already exists '}, status=status.HTTP_400_BAD_REQUEST)
  

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

       
            menu = Menu(
                name=menu_name,
                price=price,
               
                menu_day=day,
                cycle_name=cycle_name,
                menu_date=menu_date,
                category=category
            )
            menu.save()
            created_menus.append(MenuSerializer(menu).data)

    return Response({'message': 'Menus created successfully!', 'menus': created_menus}, status=status.HTTP_201_CREATED)

@api_view(['POST', 'PUT', 'DELETE'])
def get_cycle_menus(request):
    cycle_name = request.data.get('cycle_name')

    
    if not cycle_name:
        return Response({'error': 'Cycle name is required'}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':
        
        menus = Menu.objects.filter(cycle_name=cycle_name)

        if not menus.exists():
            return Response({'error': f'No menus found for cycle name: {cycle_name}'}, status=status.HTTP_404_NOT_FOUND)

        
        serialized_menus = MenuSerializer(menus, many=True)

        return Response({'message': 'Menus fetched successfully!', 'menus': serialized_menus.data}, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
      
        menus = Menu.objects.filter(cycle_name=cycle_name)

        if not menus.exists():
            return Response({'error': f'No menus found for cycle name: {cycle_name}'}, status=status.HTTP_404_NOT_FOUND)

        
        updated_data = request.data.get('updated_data')

        if not updated_data:
            return Response({'error': 'No data provided for updating menus'}, status=status.HTTP_400_BAD_REQUEST)

        updated_menus = []
        for menu_item in menus:
           
            menu_data = updated_data.get(str(menu_item.id))

            if menu_data:
                menu_item.name = menu_data.get('name', menu_item.name)
                menu_item.price = menu_data.get('price', menu_item.price)

                
                menu_item.save()
                updated_menus.append(MenuSerializer(menu_item).data)

        return Response({'message': 'Menus updated successfully!', 'menus': updated_menus}, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        
        menus = Menu.objects.filter(cycle_name=cycle_name)

     
        if not menus.exists():
            return Response({'error': f'No menus found for cycle name: {cycle_name}'}, status=status.HTTP_404_NOT_FOUND)

        deleted_count, _ = menus.delete()

        return Response({'message': f'{deleted_count} menus deleted successfully.'}, status=status.HTTP_200_OK)
@api_view(['GET'])
def get_all_cycles_with_menus(request):
   
    cycle_names = Menu.objects.values_list('cycle_name', flat=True).distinct()


    if not cycle_names:
        return Response({'error': 'No cycle names found'}, status=status.HTTP_404_NOT_FOUND)
    
    cycles_with_menus = []

    
    for cycle_name in cycle_names:
        menus = Menu.objects.filter(cycle_name=cycle_name)
        
        
        serialized_menus = MenuSerializer(menus, many=True)
       
        cycles_with_menus.append({
            'cycle_name': cycle_name,
            'menus': serialized_menus.data
        })
    
    return Response({'message': 'Cycles and their menus fetched successfully!', 'cycles': cycles_with_menus}, status=status.HTTP_200_OK)
