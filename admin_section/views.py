from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from .serializers import *
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter
from django.db.models import Count
import calendar
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth.hashers import make_password
from .models import *
# Create your views here.

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
    if StudentRegisteration.objects.filter(email=email).exists():
        return Response({"error": "Email already registered as student."}, status=status.HTTP_400_BAD_REQUEST)
    if CanteenStaff.objects.filter(email=email).exists():
        return Response({"error": "Email already registered as canteen."}, status=status.HTTP_400_BAD_REQUEST)

    # Choose the correct serializer based on user type
    if user_type == "parent":
        serializer = ParentRegisterationSerializer(data=request.data)
    elif user_type == "student":
        serializer = StudentRegisterationSerializer(data=request.data)
    elif user_type == "staff":
        serializer = StaffRegisterationSerializer(data=request.data)
    elif user_type == "canteenstaff":
        
        serializer = CanteenStaffSerializer(data=request.data, context={'school_id': request.data.get('school_id')})
    else:
        return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

    password = request.data.get('password')
    password_confirmation = request.data.get('password_confirmation')

    if password != password_confirmation:
        return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)


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


# Get All user by 1
# @api_view(['GET'])
# def get_user_by_id(request, user_id, user_type):
#     """
#     Fetch user details by user_id and user_type.
#     user_type can be 'parent', 'student', 'staff', or 'secondary_student'.
#     """
#     if user_type == 'parent':
#         user = ParentRegisteration.objects.filter(id=user_id).first()
#         if not user:
#             return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)
#         serializer = ParentRegisterationSerializer(user)
    
#     elif user_type == 'student':
#         # First, fetch the primary student
#         user = StudentRegisteration.objects.filter(id=user_id).first()
#         if not user:
#             return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
#         serializer = StudentRegisterationSerializer(user)
    
#     elif user_type == 'staff':
#         user = StaffRegisteration.objects.filter(id=user_id).first()
#         if not user:
#             return Response({'error': 'Staff not found.'}, status=status.HTTP_404_NOT_FOUND)
#         serializer = StaffRegisterationSerializer(user)
    
#     elif user_type == 'secondary_student':
#         # Now, for secondary students, we use the SecondaryStudent model
#         user = SecondaryStudent.objects.filter(id=user_id).first()
#         if not user:
#             return Response({'error': 'Secondary student not found.'}, status=status.HTTP_404_NOT_FOUND)
#         serializer = SecondaryStudentSerializer(user)
    
#     else:
#         return Response({'error': 'Invalid user type. Must be one of: parent, student, staff, or secondary_student.'}, status=status.HTTP_400_BAD_REQUEST)

#     return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_parent_by_id(request, parent_id):
    # Fetch the parent registration by parent ID
    parent = get_object_or_404(ParentRegisteration, id=parent_id)

    # Fetch the student info related to the teacher of this parent (assuming ParentRegisteration model has a field linking to Teacher)
    student_info = Student.objects.filter(teacher__id=parent.id).first()

    # Start preparing the response data
    response_data = {
        'parent_first_name': parent.first_name,
        'parent_last_name': parent.last_name,
        'parent_email': parent.email,
    }

    if student_info:
        # Fetching child details from the Student model
        response_data['child_class'] = student_info.class_year
        response_data['child_name'] = student_info.student_name
        response_data['child_school'] = student_info.school.name  # Assuming 'school' is a ForeignKey to PrimarySchool
        response_data['child_allergy'] = student_info.allergy
    else:
        response_data['child_class'] = None
        response_data['child_name'] = None
        response_data['child_school'] = None
        response_data['child_allergy'] = None

    return Response(response_data)

@api_view(['GET'])
def get_staff_by_id(request, staff_id):
    staff = get_object_or_404(StaffRegisteration, id=staff_id)

    # Fetch all students associated with the staff (teacher) through the Class model
    students_info = Class.objects.filter(teacher=staff)

    # Prepare response data
    response_data = {
        'staff_first_name': staff.first_name,
        'staff_last_name': staff.last_name,
        'staff_email': staff.email,
        'staff_phone_no': staff.phone_no,
        # Remove or change the following line to match the data you have for staff school
        # 'staff_school': staff.school.name,  
        'staff_allergy': staff.allergy if hasattr(staff, 'allergy') else None,
    }

    children_data = []
    for class_info in students_info:
        student = class_info.student  # Get the student linked to this class
        children_data.append({
            'child_name': student.first_name + ' ' + student.last_name,
            'child_class': student.class_year,
            'child_allergy': student.allergy,
        })

    response_data['children'] = children_data
    return Response(response_data)

# Student API: Fetch Student Info
# @api_view(['GET'])
# def get_student_by_id(request, student_id):
#     student = get_object_or_404(StudentRegisteration, id=student_id)

#     # Fetch detailed information from the Student model
#     student_details = Student.objects.filter(id=student.id).first()

#     response_data = {
#         'student_first_name': student.first_name,
#         'student_last_name': student.last_name,
#         'student_email': student.email,
#     }

#     if student_details:
#         response_data['student_class'] = student_details.class_year
#         response_data['student_school'] = student_details.school.name  # Assuming Student model has a school field
#         response_data['student_allergy'] = student_details.allergy

#     return Response(response_data)
@api_view(['GET'])
def get_student_by_id(request, student_id):
    # Fetch the student details by student_id
    student = get_object_or_404(Student, id=student_id)

    # Prepare the response data
    response_data = {
        'student_name': student.student_name,
        'class_year': student.class_year,
        'student_email': student.student_email,
        'school': student.school.school_name,  # Assuming the 'school' field is a ForeignKey to the PrimarySchool model
        'teacher': student.teacher.teacher_name,  # Assuming 'teacher' is a ForeignKey to Teacher model
    }

    return Response(response_data)

  
    
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


# For Primary School Student
@api_view(['GET','POST'])
def get_student_detail(request, school_id,):
    school = get_object_or_404(PrimarySchool, pk=school_id)
   
    if request.method == 'GET':
       student = Student.objects.filter(school=school)
       student_serializer = StudentSerializer(student, many=True)
       return Response(student_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        student_name = request.data.get('student_name')
        class_year = request.data.get('class_year')
        teacher_id = request.data.get('teacher_id')

        teacher=get_object_or_404(Teacher,pk=teacher_id)
        new_student = Student(
            student_name=student_name,
            class_year=class_year,
            school=school,
            teacher=teacher
        )
        new_student.save()
        student_serializer = StudentSerializer(new_student)
        return Response(student_serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'DELETE'])
def update_delete_student(request, school_id, student_id):
    school = get_object_or_404(PrimarySchool, pk=school_id)
    # teacher = get_object_or_404(Teacher, pk=teacher_id)
    student = get_object_or_404(Student, pk=student_id, school=school)
    # teacher=
    if request.method == 'GET':
        student_serializer = StudentSerializer(student)
        return Response(student_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        student_name = request.data.get('student_name', student.student_name)
        class_year = request.data.get('class_year', student.class_year)
        teacher= request.data.get('teacher', student.teacher)

        student.student_name = student_name
        student.class_year = class_year
        student.teacher = teacher
        student.save()

        student_serializer = StudentSerializer(student)
        return Response(student_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class StudentSearch(ListAPIView):
   queryset=Student.objects.all()
   serializer_class=StudentSerializer
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
    student = get_object_or_404(SecondaryStudent, pk=student_id, secondary_school=school)

    
    if request.method == 'GET':
        student_serializer = SecondaryStudentSerializer(student)
        return Response(student_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        student_name = request.data.get('secondary_student_name', student.secondary_student_name)
        class_year = request.data.get('secondary_class_year', student.secondary_class_year)

        student.secondary_student_name = student_name
        student.secondary_class_year = class_year
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

# Menu
@api_view(['POST'])
def add_menu(request):
    if request.method == 'POST':
       
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
        cycle_name = request.data.get('cycle_name') 
        menu_date = datetime.now().date()  

        # Validate cycle_name
        if not cycle_name.isalnum() and " " not in cycle_name:
            return Response({'error': 'Cycle Name cannot contain special characters!'}, status=status.HTTP_400_BAD_REQUEST)
        if school_type == 'primary':
            if Menu.objects.filter(cycle_name=cycle_name, primary_school__id=school_id).exists():
                return Response({'error': f'Menu with cycle name "{cycle_name}" already exists for Primary School.'}, status=status.HTTP_400_BAD_REQUEST)
        elif school_type == 'secondary':
            if Menu.objects.filter(cycle_name=cycle_name, secondary_school__id=school_id).exists():
                return Response({'error': f'Menu with cycle name "{cycle_name}" already exists for Secondary School.'}, status=status.HTTP_400_BAD_REQUEST)


        school_model = PrimarySchool if school_type == 'primary' else SecondarySchool
        school = school_model.objects.filter(id=school_id).first()

        if not school:
            return Response({'error': f'{school_type.capitalize()} School not found'}, status=status.HTTP_404_NOT_FOUND)
        created_menus = []

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for day in days:
            categories = request.data.get(f'category_{day}')
            item_names = request.data.get(f'item_names_{day}')
            prices = request.data.get(f'price_{day}')
            if not all([categories, item_names, prices]):
                return Response({'error': f'Missing data for {day}. Ensure all fields are included.'}, status=status.HTTP_400_BAD_REQUEST)

            for category_id, item_name, price in zip(categories, item_names, prices):
                
                try:
                    price = float(price)
                    if price < 0:
                        raise ValueError
                except ValueError:
                    return Response({'error': f'Invalid price for {item_name} on {day}.'}, status=status.HTTP_400_BAD_REQUEST)

               
                category = Categories.objects.filter(id=category_id).first()
                if not category:
                    return Response({'error': f'Category with ID {category_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)

                is_active_time = datetime.now()   
                menu_data = {
                    'name': item_name,
                    'price': price,
                    'menu_day': day,
                    'cycle_name': cycle_name,
                    'menu_date': menu_date,
                    'primary_school': school.id if school_type == 'primary' else None,
                    'secondary_school': school.id if school_type == 'secondary' else None,
                    'category': category.id,  
                    'is_active_time': is_active_time,  
                   
                }
                if school_type == 'primary':
                    menu_data['secondary_school'] = None
                elif school_type == 'secondary':
                    menu_data['primary_school'] = None

              
                menu_serializer = MenuSerializer(data=menu_data)
                if not menu_serializer.is_valid():
                    return Response(menu_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                # Save the menu item
                menu_instance = menu_serializer.save()
                created_menus.append({
                    'id': menu_instance.id,
                    'name': menu_instance.name,
                    'price': str(menu_instance.price),
                    'menu_day': menu_instance.menu_day,
                    'menu_date': str(menu_instance.menu_date),
                    'cycle_name': menu_instance.cycle_name,
                    'is_active': menu_instance.is_active  
                })
        return Response({
            'message': 'Menus created successfully!',
            'menus': created_menus
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def activate_cycle(request):
    if request.method == 'POST':
        # Get data from request
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
        cycle_name = request.data.get('cycle_name')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
       
        if not cycle_name.isalnum() and " " not in cycle_name:
            return Response({'error': 'Cycle Name cannot contain special characters!'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)


        school_model = PrimarySchool if school_type == 'primary' else SecondarySchool
        school = school_model.objects.filter(id=school_id).first()

        if not school:
            return Response({'error': f'{school_type.capitalize()} School not found'}, status=status.HTTP_404_NOT_FOUND)
        
        menus = Menu.objects.filter(
            cycle_name=cycle_name,
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None
        )

        if not menus:
            return Response({'error': f'No menus found for cycle "{cycle_name}" in the specified school.'}, status=status.HTTP_404_NOT_FOUND)

        updated_menus = []
        for menu in menus:
            menu.start_date = start_date
            menu.end_date = end_date
            menu.save()
            updated_menus.append({
                'id': menu.id,
                'name': menu.name,
                'price': str(menu.price),
                'menu_day': menu.menu_day,
                'cycle_name': menu.cycle_name,
                'start_date': str(menu.start_date),
                'end_date': str(menu.end_date),
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

        # Validate required fields
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

        # Validate required fields
        if not school_id or not school_type or not cycle_name:
            return Response({'error': 'school_id, school_type, and cycle_name are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the corresponding school model
        if school_type == 'primary':
            school = PrimarySchool.objects.filter(id=school_id).first()  
        elif school_type == 'secondary':
            school = SecondarySchool.objects.filter(id=school_id).first()
        else:
            return Response({'error': 'Invalid school_type. Use "primary" or "secondary".'}, status=status.HTTP_400_BAD_REQUEST)

        if not school:
            return Response({'error': f'{school_type.capitalize()} school with ID {school_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Filter menus based on the provided cycle_name and school
        menus_to_delete = Menu.objects.filter(
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None,
            cycle_name=cycle_name
        )

        if start_date and end_date:
            menus_to_delete = menus_to_delete.filter(start_date__lte=start_date, end_date__gte=end_date)

        if not menus_to_delete.exists():
            return Response({'error': f'No menus found for cycle "{cycle_name}" in the specified school.'}, status=status.HTTP_404_NOT_FOUND)

        # Delete the menus
        menus_to_delete.delete()

        return Response({'message': f'All menus for cycle "{cycle_name}" in school {school_id} have been deleted.'}, status=status.HTTP_204_NO_CONTENT)

    return Response({'error': 'Invalid request method.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
@api_view(['GET', 'PATCH'])
def edit_menu(request, id):
    print(f"Received request to edit menu item with id: {id}")
    if request.method == 'GET':
    
        try:
            menu_item = Menu.objects.get(id=id)
        except Menu.DoesNotExist:
            return Response({'error': 'Menu item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = MenuSerializer(menu_item)
        return Response({'menu': serializer.data}, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
      
        try:
            menu_item = Menu.objects.get(id=id)
        except Menu.DoesNotExist:
            return Response({'error': 'Menu item not found'}, status=status.HTTP_404_NOT_FOUND)

        category_id = request.data.get('category')
        menu_name = request.data.get('name')
        price = request.data.get('price')
        if category_id:
            try:
                category = Categories.objects.get(id=category_id)
            except Categories.DoesNotExist:
                return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
            menu_item.category = category
        if menu_name:
            menu_item.name = menu_name
        
        if price is not None:
            menu_item.price = price

        menu_item.save()

        serializer = MenuSerializer(menu_item)
        return Response({'message': 'Menu updated successfully!', 'menu': serializer.data}, status=status.HTTP_200_OK)


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
@api_view(['GET', 'PATCH'])
def update_menu_items(request, pk):
    menu_item = get_object_or_404(MenuItems, pk=pk)
    
    if request.method == 'GET':
        serializer = MenuItemsSerializer(menu_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = MenuItemsSerializer(menu_item, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View Registered Students
@csrf_exempt
@api_view(['GET'])
def view_students(request):
    search_query = request.query_params.get('search', None) 

    try:
    
        primary_students = Student.objects.all()
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

   
    primary_students_serializer = StudentSerializer(primary_students, many=True)
    secondary_students_serializer = SecondaryStudentSerializer(secondary_students, many=True)
    primary_students_data = primary_students_serializer.data
    for student in primary_students_data:
        student['school_type'] = 'Primary'
        

    secondary_students_data = secondary_students_serializer.data
    for student in secondary_students_data:
        student['school_type'] = 'Secondary'
       

    return Response({
        'primary_students': primary_students_data,
        'secondary_students': secondary_students_data
    }, status=status.HTTP_200_OK)



@api_view(['PUT', 'GET'])
def edit_student(request, student_id):
    try:
      
        student = Student.objects.get(id=student_id)
        school_type = 'primary'
        serializer = StudentSerializer(student, data=request.data, partial=True)
    except Student.DoesNotExist:
     
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
        # Extracting input fields from the request data
        user_type = request.data.get('user_type')
        user_id = request.data.get('user_id')
        selected_days = request.data.get('selected_days')
        child_id = request.data.get('child_id', None)  # Optional child_id for parents/staff
        quantities = request.data.get('quantities', [])  

        # Validation checks
        if not user_type or not user_id or not selected_days:
            return Response({'error': 'User type, user ID, and selected days are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(quantities) != len(selected_days):
            return Response({'error': 'The number of quantities should match the number of selected days.'}, status=status.HTTP_400_BAD_REQUEST)

        # Handle different user types
        user = None
        if user_type == 'student':
            user = StudentRegisteration.objects.filter(id=user_id).first()
        elif user_type == 'parent':
            user = ParentRegisteration.objects.filter(id=user_id).first()
        elif user_type == 'staff':
            user = StaffRegisteration.objects.filter(id=user_id).first()

        if not user:
            return Response({'error': f'{user_type.capitalize()} not found.'}, status=status.HTTP_404_NOT_FOUND)

        created_orders = []  # To store created orders
        
        # Iterate over the selected days
        for day, quantity in zip(selected_days, quantities):
            menus_for_day = Menu.objects.filter(menu_day__iexact=day)

            if not menus_for_day:
                return Response({'error': f'No menus available for {day}.'}, status=status.HTTP_404_NOT_FOUND)

            order_total_price = 0
            order_items = []  

            # Create order data
            order_data = {
                'user_id': user.id,
                'user_type': user_type,
                'total_price': order_total_price,
                'week_number': datetime.now().isocalendar()[1],
                'year': datetime.now().year,
                'order_date': datetime.now(),
                'selected_day': day,
                'is_delivered': False,
                'status': 'pending',
            }

            # Add child_id if applicable
            if user_type == 'parent' and child_id:
                order_data['child_id'] = child_id
            elif user_type == 'staff' and child_id:
                order_data['child_id'] = child_id

            # Serialize and save the order
            order_serializer = OrderSerializer(data=order_data)
            if not order_serializer.is_valid():
                return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            order_instance = order_serializer.save()

            # Add menu items to the order and handle quantities
            for menu_item in menus_for_day:
                order_item = OrderItem.objects.create(
                    menu=menu_item,
                    quantity=quantity,  # Directly using the passed quantity
                    order=order_instance
                )
                order_items.append(order_item)
                order_total_price += menu_item.price * quantity  # Adjust total price based on quantity

            # Update total price after adding items
            order_instance.total_price = order_total_price
            order_instance.save()

            # Prepare the order response details
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
                        'item_name': item.menu.name,  # Name of the item
                        'price': item.menu.price,     # Price of the item
                        'quantity': item.quantity     # Quantity of the item (from quantities list)
                    } for item in order_items
                ],
                'user_name': order_instance.user_name,  # Include user_name in the response
            }

            if order_instance.user_type in ['parent', 'staff']:
                order_details['child_id'] = order_instance.child_id  # Include child_id for parents/staff

            created_orders.append(order_details)

        return Response({
            'message': 'Orders created successfully!',
            'orders': created_orders
        }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def complete_order(request):
    # Extract the order ID from the request data
    order_id = request.data.get('order_id')

    if not order_id:
        return Response({'error': 'Order ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch the order by ID
        order = Order.objects.get(id=order_id)

        # Mark the order as completed
        order.is_delivered = True
        order.status = 'done'
        order.save()

        # Respond with success and order details
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
    # Extract the order ID from the request data
    order_id = request.data.get('order_id')

    if not order_id:
        return Response({'error': 'Order ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch the order by ID
        order = Order.objects.get(id=order_id)

        # Mark the order as cancelled
        order.status = 'cancelled'
        order.is_delivered = False
        order.save()

        # Respond with success and order details
        return Response({
            'message': 'Order cancelled successfully!',
            'order_id': order.id,
            'status': order.status,
            'is_delivered': order.is_delivered,
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
def get_all_orders(request):
    # Fetch all orders from the database
    orders = Order.objects.all()

    if not orders.exists():
        return Response({'error': 'No orders found.'}, status=status.HTTP_404_NOT_FOUND)

    order_details = []

    # Iterate through each order to fetch the related order items and other details
    for order in orders:
        order_items = OrderItem.objects.filter(order=order)
        order_items_data = [
            {
                'item_name': item.menu.name,  # Name of the menu item
                'price': item.menu.price,     # Price of the menu item
                'quantity': item.quantity     # Quantity of the item in the order
            } for item in order_items
        ]

        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': str(order.order_date),
            'status': order.status,
            'week_number': order.week_number,
            'year': order.year,
            'items': order_items_data,
            'user_name': order.user_name,  # The name of the user who made the order
        }

        # If the order belongs to a parent or staff, include child_id
        if order.user_type in ['parent', 'staff']:
            order_data['child_id'] = order.child_id  # Include child_id for parents/staff

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
        order_items_data = [
            {
                'item_name': item.menu.name,  
                'price': item.menu.price,    
                'quantity': item.quantity     
            } for item in order_items
        ]

        
        order_data = {
            'order_id': order.id,
            'selected_day': order.selected_day,
            'total_price': order.total_price,
            'order_date': str(order.order_date),
            'status': order.status,
            'week_number': order.week_number,
            'year': order.year,
            'items': order_items_data,
            'user_name': order.user_name, 
        }

        
        if order.user_type in ['parent', 'staff']:
            order_data['child_id'] = order.child_id

        return Response({
            'message': 'Order retrieved successfully!',
            'order': order_data
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