import jwt
import requests
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
from urllib.parse import quote
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils.crypto import get_random_string
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
from openpyxl.utils import get_column_letter
from django.core.files.storage import FileSystemStorage
from datetime import datetime,timedelta
from django.http import HttpResponse,JsonResponse
from django.db.models import Count
from rest_framework.exceptions import NotFound
import calendar
import stripe
import zipfile
from io import BytesIO
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
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY
ALLOWED_FILE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
from .models import Allergens

from django.utils import timezone
from datetime import timedelta

@api_view(["POST"])
def register(request):
    email = request.data.get("email")
    login_method = request.data.get("login_method", "email")  # default to email if not provided

    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if already registered
    if StaffRegisteration.objects.filter(email=email).exists() or \
       ParentRegisteration.objects.filter(email=email).exists() or \
       SecondaryStudent.objects.filter(email=email).exists() or \
       CanteenStaff.objects.filter(email=email).exists():
        return Response({"error": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

    existing_unverified = UnverifiedUser.objects.filter(email=email).first()

    # Handle recent attempts (only apply for email flow)
    if existing_unverified:
        if login_method == "email":
            if existing_unverified.created_at > timezone.now() - timedelta(seconds=60):
                return Response(
                    {"error": "A verification email has already been sent recently. Please check your inbox."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        # Delete any old unverified user regardless of method
        existing_unverified.delete()

    # Create new unverified user (for both email and social logins)
    new_unverified = UnverifiedUser.objects.create(
        email=email,
        data=request.data,
        login_method=login_method
    )

    # If it's email login, send verification email
    if login_method == "email":
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{new_unverified.token}/"
        send_mail(
            subject="Action Required: Confirm Your Email Address",
            message=f"""
Hi there,

Thank you for registering with us.

To complete your registration, please confirm your email address by clicking the link below:

{verification_link}

If you did not create an account with us, you can safely ignore this email.

Best regards,  
The Rafters Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        return Response(
            {"message": "Verification email sent. Please check your inbox."},
            status=status.HTTP_200_OK
        )

    # For social login flow
    return Response(
        {
            "message": "OAuth login successful. Additional info required.",
            "token": str(new_unverified.token),
            "provider": login_method
        },
        status=status.HTTP_200_OK
    )


# Using your custom token generator
custom_token_generator = CustomPasswordResetTokenGenerator()

custom_token_generator = CustomPasswordResetTokenGenerator()
@api_view(["GET"])
def verify_email(request, token):
    try:
        unverified = UnverifiedUser.objects.get(token=token)

        # If already verified
        if unverified.is_verified:
            return Response({"message": "This email is already verified."},
                            status=status.HTTP_200_OK)

        # Token has expired
        if timezone.now() > unverified.created_at + timedelta(hours=1):
            old_data = unverified.data
            email = old_data.get("email")

            # Delete the expired token
            unverified.delete()

            # Generate a new token and send it
            new_unverified = UnverifiedUser.objects.create(
                email=email,
                data=old_data,
            )

            new_link = f"{settings.FRONTEND_URL}/verify-email/{new_unverified.token}/"
            send_mail(
                subject="New Verification Link - Rafters",
                message=f"""Hi there,

Your previous verification link has expired. Please use the new one below:

{new_link}

This link is valid for 1 hour.

Best regards,
The Rafters Team
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )

            return Response({"error": "Verification link has expired. A new one has been sent to your email."},
                            status=status.HTTP_400_BAD_REQUEST)

        # If we reach here, the token is valid — proceed with registration
        user_data = unverified.data
        user_type = user_data.get("user_type")
        school_field = None

        if user_data.get("school_type"):
            school = PrimarySchool.objects.get(id=user_data["school_id"]) if user_data["school_type"] == "primary" else SecondarySchool.objects.get(id=user_data["school_id"])

            if user_data["user_type"] == "student":
                user_data["school"] = school.id
                serializer = SecondaryStudentSerializer(data=user_data)

            elif user_data["user_type"] == "staff":
                key = "primary_school" if user_data["school_type"] == "primary" else "secondary_school"
                user_data[key] = school.id
                serializer = StaffRegisterationSerializer(data=user_data)

            elif user_data["user_type"] == "canteenstaff":
                key = "primary_school" if user_data["school_type"] == "primary" else "secondary_school"
                user_data[key] = school.id
                serializer = CanteenStaffSerializer(data=user_data)

            else:
                return Response({"error": "Invalid user type."},
                                status=status.HTTP_400_BAD_REQUEST)

        elif user_data["user_type"] == "parent":
            serializer = ParentRegisterationSerializer(data=user_data)

        else:
            return Response({"error": "Invalid user type."},
                            status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            unverified.is_verified = True
            unverified.save()
            return Response({"message": "Email verified successfully. User account has been created."},
                            status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except UnverifiedUser.DoesNotExist:
        return Response({"error": "Invalid or non-existing verification link."},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def password_reset(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required."}, status=400)

    user = None
    for model in [ParentRegisteration, StaffRegisteration, SecondaryStudent, CanteenStaff]:
        try:
            user = model.objects.get(email=email)
            break
        except model.DoesNotExist:
            continue

    if not user:
        return Response({"error": "User not found."}, status=400)

    signer = TimestampSigner()
    signed_token = signer.sign(user.email)
    encoded_token = quote(signed_token)

    frontend_url = os.getenv('FRONTEND_URL', 'https://www.raftersfoodservices.ie/')
    reset_link = f'{frontend_url}/password-reset?token={encoded_token}'

    from_email = os.getenv('DEFAULT_FROM_EMAIL', 'support@raftersfoodservices.ie')

    send_mail(
        subject='Password Reset Request',
        message=f'Click the following link to reset your Rafters Food Services account password: {reset_link}',
        from_email=from_email,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return Response({"message": "Password reset email sent."}, status=200)

@api_view(["POST"])
def password_reset_confirm(request):
    token = request.data.get("token")
    password = request.data.get("password")

    if not token or not password:
        return Response({"error": "Token and password must be provided."}, status=400)

    try:
        signer = TimestampSigner()
        email = signer.unsign(token, max_age=3600)  # 1 hour expiry
    except (BadSignature, SignatureExpired):
        return Response({"error": "Invalid or expired token."}, status=400)

    # Find user in all models
    user = None
    user_model = None
    for model in [ParentRegisteration, StaffRegisteration, SecondaryStudent, CanteenStaff]:
        try:
            user = model.objects.get(email=email)
            user_model = model
            break
        except model.DoesNotExist:
            continue

    if not user:
        return Response({"error": "User not found."}, status=400)

    user_model.objects.filter(email=email).update(password=make_password(password))
    updated_user = user_model.objects.get(email=email)

    if not check_password(password, updated_user.password):
        return Response({"error": "Password was not set correctly."}, status=500)

    return Response({"message": "Password reset successful."}, status=200)
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
        data = serializer.data  # Serialized data

        # Add school_name field dynamically
        if staff.school_type == 'primary' and staff.primary_school:
            data['school_name'] = staff.primary_school.school_name
        elif staff.school_type == 'secondary' and staff.secondary_school:
            data['school_name'] = staff.secondary_school.secondary_school_name
        else:
            data['school_name'] = 'Unknown School'

        return Response(data, status=status.HTTP_200_OK)

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



def generate_unique_username(first_name, last_name):
    from admin_section.models import PrimaryStudentsRegister
    base_username = f"{first_name.lower()}_{last_name.lower()}"
    username = base_username
    counter = 1

    while PrimaryStudentsRegister.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    return username


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

    username = generate_unique_username(first_name, last_name)
 

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

@api_view(['GET'])
def list_all_teachers(request):
    teachers = Teacher.objects.all()
    serializer = TeacherSerializer(teachers, many=True)
    return Response({'teachers': serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
def teacher_detail(request, teacher_id):
    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return Response({'error': 'Teacher not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TeacherSerializer(teacher)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = TeacherSerializer(teacher, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Teacher updated successfully.', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        teacher.delete()
        return Response({'message': 'Teacher deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

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
       
        new_menu = Menu(
            name=menu.name,
            price=menu.price,
            cycle_name=menu.cycle_name,
            menu_day=menu.menu_day,
            menu_date=menu.menu_date,
            category=menu.category,
        )

       
        if school_type == 'primary':
            new_menu.primary_school = school
            new_menu.secondary_school = None
        elif school_type == 'secondary':
            new_menu.secondary_school = school
            new_menu.primary_school = None  

       
        new_menu.save()
        updated_menus.append(MenuSerializer(new_menu).data)

    return Response({'message': 'Menus assigned to school successfully!', 'menus': updated_menus}, status=status.HTTP_200_OK)

@api_view(['POST'])
def activate_cycle(request):
    if request.method == 'POST':
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
        cycle_name = request.data.get('cycle_name')
        
        # [Validation code remains the same]
        
        # Determine the school model based on school type
        school_model = PrimarySchool if school_type == 'primary' else SecondarySchool
        school = school_model.objects.filter(id=school_id).first()
        
        if not school:
            return Response({'error': f'{school_type.capitalize()} School not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Deactivate only the active menus for THIS specific school
        if school_type == 'primary':
            Menu.objects.filter(primary_school=school, is_active=True).update(is_active=False)
        else:
            Menu.objects.filter(secondary_school=school, is_active=True).update(is_active=False)
        
        # Find source menus for the specified cycle
        source_menus = Menu.objects.filter(
            cycle_name=cycle_name,
        )
        
        if not source_menus.exists():
            return Response({'error': f'No menus found for cycle "{cycle_name}".'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create or update menus specifically for this school
        updated_menus = []
        for source_menu in source_menus:
            # Check if this menu already exists for this school
            school_field = 'primary_school' if school_type == 'primary' else 'secondary_school'
            filter_params = {
                'name': source_menu.name,
                'menu_day': source_menu.menu_day,
                'cycle_name': source_menu.cycle_name,
                school_field: school
            }
            
            # Try to find existing menu or create a new one
            existing_menu = Menu.objects.filter(**filter_params).first()
            
            if existing_menu:
                # Update existing menu
                existing_menu.is_active = True
                existing_menu.price = source_menu.price
                # Update other fields as needed
                existing_menu.save()
                menu = existing_menu
            else:
                # Create a new menu for this school
                menu_data = {
                    'name': source_menu.name,
                    'price': source_menu.price,
                    'menu_day': source_menu.menu_day,
                    'cycle_name': source_menu.cycle_name,
                    'is_active': True
                }
                
                if school_type == 'primary':
                    menu_data['primary_school'] = school
                else:
                    menu_data['secondary_school'] = school
                
                menu = Menu.objects.create(**menu_data)
            
            updated_menus.append({
                'id': menu.id,
                'name': menu.name,
                'price': str(menu.price),
                'menu_day': menu.menu_day,
                'cycle_name': menu.cycle_name,
                'is_active': menu.is_active
            })
        
        return Response({
            'message': f'Cycle "{cycle_name}" activated successfully for {school.school_name if school_type == "primary" else school.secondary_school_name}!',
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

    try:
        if school_type == 'primary':
            menus = Menu.objects.filter(
                primary_school_id=school_id
            ).select_related('category', 'primary_school')
            
            subquery = Menu.objects.filter(
                primary_school_id=school_id
            ).values('cycle_name').distinct()

        elif school_type == 'secondary':
            menus = Menu.objects.filter(
                secondary_school_id=school_id
            ).select_related('category', 'secondary_school')
            
            subquery = Menu.objects.filter(
                secondary_school_id=school_id
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
                        "allergies": [allergy.allergy for allergy in item.allergies.all()],
                        "image_url": request.build_absolute_uri(item.image.url) if item.image else None
                    })

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
@parser_classes([JSONParser])  # Use JSONParser here as you're sending JSON data
def add_menu_item(request):
    if request.method == 'POST':
        serializer = MenuItemsSerializer(data=request.data, context={'request': request})
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
        order.status = 'collected'
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

        # HTML email content
        html_message = f"""
        <html>
            <body>
                <h2 style="color:#4CAF50;">New Contact Message</h2>
                <p><strong>Name:</strong> {full_name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Phone:</strong> {phone if phone else 'Not provided'}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Message:</strong></p>
                <blockquote style="border-left: 4px solid #4CAF50; padding-left: 15px;">
                    {message}
                </blockquote>
                <p><em>We will respond to you shortly. Thank you for reaching out!</em></p>
            </body>
        </html>
        """

        send_mail(
            subject=f"New Contact Message: {subject}",
            message=message,  # Plain text message (you can remove this if you want only HTML email)
            from_email=settings.DEFAULT_FROM_EMAIL,  
            recipient_list=[settings.MAIL_DEFAULT_SENDER],  # This will send to the email set in MAIL_DEFAULT_SENDER
            fail_silently=False,
            html_message=html_message  # Include HTML content
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

            if user_type in ['parent', 'staff'] and child_id:
                for order in created_orders:
                    order['status'] = 'paid'
                return Response({
                    'message': 'Orders created successfully with free meal for child.',
                    'orders': created_orders
                }, status=status.HTTP_201_CREATED)
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
    current_time = datetime.now()
    current_week_number = current_time.isocalendar()[1]
    current_year = current_time.year
    
    # Check if we're past the Friday 2PM cutoff
    is_past_cutoff = (
        current_time.weekday() == 4 and current_time.hour >= 14  # Friday 2PM+
    ) or current_time.weekday() > 4  # Saturday/Sunday
    
    # Determine target week
    if is_past_cutoff:
        target_week = current_week_number + 1
        # Handle year transition
        if target_week > 52:
            target_week = 1
            current_year += 1
    else:
        target_week = current_week_number
    filter_kwargs = {
        'week_number': target_week,
        'year': current_year
    }
    
    if school_type == 'primary':
        filter_kwargs['primary_school_id'] = school_id
    else:
        filter_kwargs['secondary_school_id'] = school_id

    orders = Order.objects.filter(**filter_kwargs).order_by('-order_date')

    student_orders = orders.exclude(user_type="staff") 
    staff_orders = orders.filter(user_type="staff")  

    print(f"🔍 Total {school_type} student orders: {student_orders.count()}")
    print(f"👨‍🏫 Total {school_type} staff orders: {staff_orders.count()}")

    return student_orders, staff_orders
def generate_workbook(school, student_orders, staff_orders, school_type, role='admin', day_filter=None):
    # Create a new workbook and remove the default sheet
    workbook = Workbook()
    workbook.remove(workbook.active)

    # Initialize data structures
    day_totals = defaultdict(lambda: defaultdict(int))
    grouped_orders = defaultdict(lambda: defaultdict(list))
    staff_orders_by_day = defaultdict(list)

    # Style definitions
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    title_font = Font(bold=True, size=14, color="000000")
    title_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    def apply_header_styling(sheet, title_text, columns):
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=len(columns))
        title_cell = sheet.cell(row=1, column=1, value=title_text)
        title_cell.font = title_font
        title_cell.fill = title_fill
        title_cell.alignment = center_align

        for col_num, column_title in enumerate(columns, 1):
            cell = sheet.cell(row=2, column=col_num, value=column_title)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_align
            sheet.column_dimensions[get_column_letter(col_num)].width = 25

    def apply_data_styling(sheet, start_row):
        for row in sheet.iter_rows(min_row=start_row):
            for cell in row:
                cell.border = border
                cell.alignment = left_align if cell.column == 1 else center_align

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
        else:
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

    all_days = list(DAY_COLORS.keys())
    days_to_generate = [day_filter] if day_filter in all_days else all_days

    for day in days_to_generate:
        # Generate class/teacher sheets
        if role in ['admin', 'staff']:
            entity_list = Teacher.objects.filter(school=school) if school_type == 'primary' else CLASS_YEARS
            for entity in entity_list:
                entity_name = entity.teacher_name if school_type == 'primary' else entity
                sheet_title = f"{entity_name} - {day}"[:31]
                sheet = workbook.create_sheet(title=sheet_title)
                sheet.sheet_properties.tabColor = DAY_COLORS.get(day, "FFFFFF")

                title = f"{entity_name} Order Sheet for {day} of {school}" if school_type == 'primary' else f"Class {entity_name} Order Sheet for {day} of {school}"
                apply_header_styling(sheet, title, ["Student Name", "Menu Items", "Quantity"])

                row_num = 3
                for order_data in grouped_orders.get(day, {}).get(entity_name, []):
                    for menu_name, quantity in order_data['order_items'].items():
                        sheet.cell(row=row_num, column=1, value=order_data['student_name'])
                        sheet.cell(row=row_num, column=2, value=menu_name)
                        sheet.cell(row=row_num, column=3, value=quantity)
                        row_num += 1

                if row_num == 3:
                    sheet.cell(row=3, column=1, value="No orders")
                    sheet.merge_cells(start_row=3, end_row=3, start_column=1, end_column=3)

                apply_data_styling(sheet, 3)

        # Staff Sheet
        if role == 'admin':
            sheet = workbook.create_sheet(title=f"Staff {day}")
            sheet.sheet_properties.tabColor = "CCCCCC"
            apply_header_styling(sheet, f"Staff Order Sheet for {day} of {school}", ["Staff Name", "Menu Items", "Quantity"])

            row_num = 3
            if not staff_orders_by_day.get(day):
                sheet.cell(row=3, column=1, value="No orders")
                sheet.merge_cells(start_row=3, end_row=3, start_column=1, end_column=3)
            else:
                for order_data in staff_orders_by_day[day]:
                    for menu_name, quantity in order_data['order_items'].items():
                        sheet.cell(row=row_num, column=1, value=order_data['staff_name'])
                        sheet.cell(row=row_num, column=2, value=menu_name)
                        sheet.cell(row=row_num, column=3, value=quantity)
                        row_num += 1

            apply_data_styling(sheet, 3)

        # Chef/Total Sheet
        if role in ['admin', 'chef']:
            sheet = workbook.create_sheet(title=f"{day} Total")
            sheet.sheet_properties.tabColor = "FFD700"
            apply_header_styling(sheet, f"Chef Order Sheet for {day} of {school}", ["Menu Item", "Total Quantity"])

            row_num = 3
            if day in day_totals:
                for menu_name, quantity in sorted(day_totals[day].items()):
                    sheet.cell(row=row_num, column=1, value=menu_name)
                    sheet.cell(row=row_num, column=2, value=quantity)
                    row_num += 1
            else:
                sheet.cell(row=3, column=1, value="No orders")
                sheet.merge_cells(start_row=3, end_row=3, start_column=1, end_column=2)

            apply_data_styling(sheet, 3)

        # Canteen Staff Day Total
        if role in ['admin', 'staff']:
            sheet = workbook.create_sheet(title=f"Canteen Total {day}")
            sheet.sheet_properties.tabColor = "92D050"
            apply_header_styling(
                sheet,
                f"Canteen Staff Sheet for {day} of {school}",
                ["Teacher/Class Year", "Student Name", "Menu Item", "Quantity"]
            )

            row_num = 3
            orders_by_group = grouped_orders.get(day, {})
            
            valid_keys = [key if key is not None else "Unknown" for key in orders_by_group.keys()]
            for group_key in sorted(valid_keys):
                student_orders = orders_by_group.get(group_key, []) or orders_by_group.get(None, [])
                sorted_student_orders = sorted(student_orders, key=lambda x: x['student_name'] or "")

                for order_data in sorted_student_orders:
                    student_name = order_data['student_name']
                    for menu_name, quantity in order_data['order_items'].items():
                        sheet.cell(row=row_num, column=1, value=group_key)
                        sheet.cell(row=row_num, column=2, value=student_name)
                        sheet.cell(row=row_num, column=3, value=menu_name)
                        sheet.cell(row=row_num, column=4, value=quantity)
                        row_num += 1

            if row_num == 3:
                sheet.cell(row=3, column=1, value="No orders")
                sheet.merge_cells(start_row=3, end_row=3, start_column=1, end_column=4)

            apply_data_styling(sheet, 3)


    return workbook

@api_view(['POST'])
def download_menu(request):
    try:
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
        role = request.data.get('role', 'admin')
        day_filter = request.data.get('day')

        if not school_id or not school_type:
            return Response({'error': 'Both school_id and school_type are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if school_type not in ['primary', 'secondary']:
            return Response({'error': 'Invalid school_type.'}, status=status.HTTP_400_BAD_REQUEST)

        school = PrimarySchool.objects.get(id=school_id) if school_type == 'primary' else SecondarySchool.objects.get(id=school_id)
        student_orders, staff_orders = fetch_orders(school_id, school_type)

        if not student_orders.exists() and not staff_orders.exists():
            student_orders, staff_orders = [], []

        workbook = generate_workbook(school, student_orders, staff_orders, school_type, role=role, day_filter=day_filter)

       # Clean and normalize names
        school_name = (
            school.secondary_school_name if school_type == 'secondary' else school.school_name
        ).replace(' ', '_')

        day_part = f"{day_filter}" if day_filter else "weekly"
        filename = f"{role}_{day_part}_orderSheet_{school_name}.xlsx"

        menu_files_directory = settings.MENU_FILES_ROOT
        os.makedirs(menu_files_directory, exist_ok=True)

        file_path = os.path.join(menu_files_directory, filename)
        workbook.save(file_path)

        return Response({
            'message': 'File generated successfully!',
            'download_link': f"{settings.MENU_FILES_URL}{filename}"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def download_all_schools_menu(request):
    try:
        role = request.data.get('role')
        day_filter = request.data.get('day')

        if role not in ['admin', 'chef', 'staff']:
            return Response(
                {'error': 'Invalid role. Must be one of: admin, chef, staff.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a zip file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:

            # Process primary schools
            for school in PrimarySchool.objects.all():
                student_orders, staff_orders = fetch_orders(school.id, 'primary')
                workbook = generate_workbook(
                    school, student_orders, staff_orders, 'primary', role=role, day_filter=day_filter
                )

                school_name = school.school_name.replace(' ', '_')
                day_part = day_filter if day_filter else 'weekly'
                filename = f"primary_{school_name}_{day_part}_orders_{role}.xlsx"

                with BytesIO() as excel_buffer:
                    workbook.save(excel_buffer)
                    excel_buffer.seek(0)
                    zip_file.writestr(filename, excel_buffer.getvalue())

            # Process secondary schools
            for school in SecondarySchool.objects.all():
                student_orders, staff_orders = fetch_orders(school.id, 'secondary')
                workbook = generate_workbook(
                    school, student_orders, staff_orders, 'secondary', role=role, day_filter=day_filter
                )

                school_name = school.secondary_school_name.replace(' ', '_')
                day_part = day_filter if day_filter else 'weekly'
                filename = f"secondary_{school_name}_{day_part}_orders_{role}.xlsx"

                with BytesIO() as excel_buffer:
                    workbook.save(excel_buffer)
                    excel_buffer.seek(0)
                    zip_file.writestr(filename, excel_buffer.getvalue())

        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        day_part = day_filter if day_filter else 'weekly'
        response['Content-Disposition'] = f'attachment; filename="all_schools_{day_part}_orders_{role}.zip"'
        return response

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
    primary_schools = PrimarySchool.objects.all()
    secondary_schools = SecondarySchool.objects.all()

    schools_data = []

  
    for school in primary_schools:
        
        menus = Menu.objects.filter(primary_school_id=school.id).select_related('primary_school')

        weekly_menu = {
            "Monday": [], "Tuesday": [], "Wednesday": [],
            "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []
        }

        for menu in menus:
            day_of_week = menu.menu_day
            if day_of_week in weekly_menu:
                weekly_menu[day_of_week].append(menu)

        is_active = False
        active_cycle = None

        for day, day_menus in weekly_menu.items():
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
       
        menus = Menu.objects.filter(secondary_school_id=school.id).select_related('secondary_school')

        weekly_menu = {
            "Monday": [], "Tuesday": [], "Wednesday": [],
            "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []
        }

        for menu in menus:
            day_of_week = menu.menu_day
            if day_of_week in weekly_menu:
                weekly_menu[day_of_week].append(menu)

        is_active = False
        active_cycle = None

        for day, day_menus in weekly_menu.items():
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

    # Validate cycle name
    if not cycle_name.isalnum() and " " not in cycle_name:
        return Response({'error': 'Cycle Name cannot contain special characters!'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if a menu with the same cycle name already exists
    if Menu.objects.filter(cycle_name=cycle_name).exists():
        return Response({'error': 'A menu with the same cycle name already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    # Define the days
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    created_menus = []

    # Iterate through each day
    for day in days:
        categories = request.data.get(f'category_{day}')
        item_names = request.data.get(f'item_names_{day}')
        prices = request.data.get(f'price_{day}')

        # Skip processing for this day if any of the required fields are None, empty list, or filled with only null or empty values
        if not categories or not item_names or not prices or \
           all(val is None or val == "" for val in categories + item_names + prices):
            continue

        # Check if the data for the day is in the correct format (list of values)
        if not isinstance(categories, list) or not isinstance(item_names, list) or not isinstance(prices, list):
            return Response({'error': f'Invalid data format for {day}. Expecting lists of categories, item names, and prices.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the lengths of the lists are consistent
        if len(categories) != len(item_names) or len(item_names) != len(prices):
            return Response({'error': f'Inconsistent data length for {day}. Categories, item names, and prices must have the same number of items.'}, status=status.HTTP_400_BAD_REQUEST)

        # Process each menu item for the day
        for category_id, menu_name, price in zip(categories, item_names, prices):
            # Skip invalid or incomplete data (empty or null values)
            if category_id is None or not menu_name or price is None or price == "":
                continue

            try:
                price = float(price)
                if price < 0:
                    return Response({'error': f'Price for {menu_name} on {day} must be positive.'}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({'error': f'Invalid price format for {menu_name} on {day}.'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the category exists
            try:
                category = Categories.objects.get(id=category_id)
            except Categories.DoesNotExist:
                return Response({'error': f'Category {category_id} not found for {menu_name} on {day}.'}, status=status.HTTP_404_NOT_FOUND)

            # Create and save the menu item
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

    # Return a success response with the created menus
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
        # Fetch all menus, regardless of the is_active status
        menus = (
            Menu.objects.filter(cycle_name=cycle_name)  # Removed is_active=True
            .order_by('id') 
            .values(
                'id', 
                'cycle_name', 
                'name', 
                'category', 
                'menu_date', 
                'menu_day', 
                'price', 
                'primary_school', 
                'secondary_school'
            )
        )

        serialized_menus = list(menus)

        cycles_with_menus.append({
            'cycle_name': cycle_name,
            'menus': serialized_menus
        })

    return Response(
        {
            'message': 'Cycles and their menus fetched successfully!',
            'cycles': cycles_with_menus
        },
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
def all_users_report(request):
    data = []

    for parent in ParentRegisteration.objects.all():
        data.append({"id": parent.id, "email": parent.email, "type": "parent"})

    for student in SecondaryStudent.objects.all():
        data.append({"id": student.id, "email": student.email, "type": "student"})

    for staff in StaffRegisteration.objects.all():
        data.append({"id": staff.id, "email": staff.email, "type": "staff"})

    return Response(data)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from admin_section.models import (
    UnverifiedUser,
    ParentRegisteration,
    StaffRegisteration,
    SecondaryStudent
)

def generate_login_response(user, user_type):
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user_type": user_type,
        "user_id": user.id,
        "message": "Login successful"
    }, status=200)

@api_view(["POST"])
def social_callback_register(request):
    token = request.data.get("access_token")  # could be ID token or access token
    provider = request.data.get("provider")
    email = None

    if provider == "google":
        try:
            # Try to decode token as an ID token (JWT)
            decoded = jwt.decode(token, options={"verify_signature": False})
            email = decoded.get("email")

        except jwt.DecodeError:
            # Not an ID token — try using access token to fetch user info
            try:
                user_info_response = requests.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if user_info_response.status_code != 200:
                    return Response({"error": "Failed to fetch user info from Google"}, status=400)

                user_info = user_info_response.json()
                email = user_info.get("email")

            except Exception as e:
                return Response({"error": f"Error fetching user info: {str(e)}"}, status=400)

    if provider == "facebook":
        try:
            user_info_response = requests.get(
                "https://graph.facebook.com/me?fields=id,name,email",
                headers={"Authorization": f"Bearer {token}"}
            )
            if user_info_response.status_code != 200:
                return Response({"error": "Failed to fetch user info from Facebook"}, status=400)

            user_info = user_info_response.json()
            email = user_info.get("email")

        except Exception as e:
            return Response({"error": f"Error fetching user info: {str(e)}"}, status=400)

    if provider == "microsoft":
        try:
            resp = requests.get(
                "https://graph.microsoft.com/v1.0/me?$select=mail,userPrincipalName",
                headers={"Authorization": f"Bearer {token}"}
            )
            print("MS Graph response:", resp.status_code, resp.text)
            if resp.status_code != 200:
                return Response({"error": "Failed to fetch user info from Microsoft"}, status=400)
            user_info = resp.json()
            email = user_info.get("mail") or user_info.get("userPrincipalName")

        except Exception as e:
            return Response({"error": f"Error fetching Microsoft user info: {str(e)}"}, status=400)


    # If email couldn't be extracted
    if not email:
        return Response({"error": "Unable to fetch email from token."}, status=400)

    # If already registered, login and return JWTs
    parent = ParentRegisteration.objects.filter(email=email).first()
    if parent:
        return generate_login_response(parent, "parent")

    staff = StaffRegisteration.objects.filter(email=email).first()
    if staff:
        return generate_login_response(staff, "staff")

    student = SecondaryStudent.objects.filter(email=email).first()
    if student:
        return generate_login_response(student, "student")

    # If not registered, proceed with social signup flow
    existing_unverified = UnverifiedUser.objects.filter(email=email).first()

    if existing_unverified:
       
        existing_unverified.token = uuid.uuid4()
        existing_unverified.login_method = provider
        existing_unverified.save()
        unverified = existing_unverified
    else:
        unverified = UnverifiedUser.objects.create(
            email=email,
            data={},
            login_method=provider,
        )


    return Response({
        "message": "OAuth login successful. Additional info required.",
        "token": str(unverified.token),
        "provider": provider,
    }, status=200)


@api_view(["POST"])
def complete_social_signup(request):
    token = request.data.get("token")
    role = request.data.get("role")  
    data = request.data.get("data")
    print("🟡 Received Token:", token)
    print("🟡 Received Role:", role)
    print("🟡 Data Keys:", list(data.keys()))
    unverified = UnverifiedUser.objects.filter(
        token=token, login_method__in=["google", "facebook", "microsoft"]
    ).first()

    if not unverified:
        return Response({"error": "Invalid or expired token"}, status=400)

    # Convert allergy names to IDs
    allergy_names = data.pop("allergies", [])
    allergy_ids = list(
        Allergens.objects.filter(allergy__in=allergy_names).values_list("id", flat=True)
    )

    # Clean up
    data.pop("user_type", None)
    data.pop("schoolName", None)
    data.pop("password", None)
    data.pop("retypePassword", None)

    created_user = None

    if role == "parent":
        created_user = ParentRegisteration.objects.create(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            username=data.get("username", ""),
            email=unverified.email,
            phone_no=data.get("phone_no"),
            password="social_dummy_password"
        )

    elif role == "student":
        school_id = data.get("school_id")
        school = SecondarySchool.objects.filter(id=school_id).first()
        created_user = SecondaryStudent.objects.create(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            username=data.get("username", ""),
            email=unverified.email,
            phone_no=data.get("phone_no"),
            class_year=data.get("student_class", ""),
            school=school,
            password="social_dummy_password"
        )

    elif role == "staff":
        school_type = data.get("school_type", "").lower()
        school_id = data.get("school_id")

        primary_school = None
        secondary_school = None

        if school_type == "primary":
            primary_school = PrimarySchool.objects.filter(id=school_id).first()
        elif school_type == "secondary":
            secondary_school = SecondarySchool.objects.filter(id=school_id).first()

        created_user = StaffRegisteration.objects.create(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            username=data.get("username", ""),
            email=unverified.email,
            phone_no=data.get("phone_no"),
            password="social_dummy_password",
            primary_school=primary_school,
            secondary_school=secondary_school,
        )

    # Set allergies if applicable
    if created_user and allergy_ids:
        created_user.allergies.set(allergy_ids)

    # Remove the unverified entry
    unverified.delete()

    # JWT tokens (same as login)
    refresh = RefreshToken.for_user(created_user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    return Response({
        'access': access_token,
        'refresh': refresh_token,
        'user_type': role,
        'user_id': created_user.id,
        'message': 'Signup and login successful'
    }, status=status.HTTP_200_OK)
