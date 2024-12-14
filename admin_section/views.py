from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from .serializers import *
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter

# Create your views here.
  
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
    if request.method=="GET":
     try:
      detail=PrimarySchool.objects.all()
     except:
        return Response(status=status.HTTP_404_NOT_FOUND)
     serializer=PrimarySchoolSerializer(detail, many=True)
     return Response(serializer.data)

@api_view(['GET','DELETE','PUT'])
def delete_primary_school(request,pk):
    try:
        school = PrimarySchool.objects.get(pk=pk)  
    except PrimarySchool.DoesNotExist:
        return Response({"error": "PrimarySchool not found."}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method=="PUT":
        school=PrimarySchool.objects.get(pk=pk)
        serializer=PrimarySchoolSerializer(school,data=request.data) 
        if serializer.is_valid():
            serializer.save()
            return Response( serializer.data,status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        
    if request.method == "DELETE":
        school.delete() 
        return Response(status=status.HTTP_204_NO_CONTENT) 
    serializer = PrimarySchoolSerializer(school)
    return Response(serializer.data, status=status.HTTP_200_OK)

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


# View for handling GET, PUT, DELETE requests for a specific teacher
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
    if request.method=="GET":
     try:
      detail=SecondarySchool.objects.all()
     except:
        return Response(status=status.HTTP_404_NOT_FOUND)
     serializer=SecondarySchoolSerializer(detail, many=True)
     return Response(serializer.data)

@api_view(['GET','DELETE','PUT'])
def delete_secondary_school(request,pk):
    try:
        school = SecondarySchool.objects.get(pk=pk)  
    except SecondarySchool.DoesNotExist:
        return Response({"error": "SecondarySchool not found."}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method=="PUT":
        school=SecondarySchool.objects.get(pk=pk)
        serializer=SecondarySchoolSerializer(school,data=request.data) 
        if serializer.is_valid():
            serializer.save()
            return Response( serializer.data,status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        
    if request.method == "DELETE":
        school.delete()  
        return Response(status=status.HTTP_204_NO_CONTENT) 
    serializer = SecondarySchoolSerializer(school)
    return Response(serializer.data, status=status.HTTP_200_OK)


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

@api_view(['POST'])
def add_menu(request):
    if request.method == 'POST':
       
        school_id = request.data.get('school_id')
        school_type = request.data.get('school_type')
        cycle_name = request.data.get('cycle_name')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')  
        menu_date = datetime.now().date()  

        # Validate cycle_name
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
                    'start_date': start_date,  
                    'end_date': end_date, 
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

      
@api_view(['POST', 'GET', 'DELETE'])
def get_complete_menu(request):
    if request.method == 'POST':

        school_type = request.data.get('school_type')  
        cycle_name = request.data.get('cycle_name')
        start_date = request.data.get('start_date')  
        end_date = request.data.get('end_date')  

       
        if not school_type or not cycle_name:
            return Response({'error': 'Both school_type and cycle_name are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if school_type == 'primary':
            school = PrimarySchool.objects.first() 
        elif school_type == 'secondary':
            school = SecondarySchool.objects.first()  
        else:
            return Response({'error': 'Invalid school_type. Use "primary" or "secondary".'}, status=status.HTTP_400_BAD_REQUEST)
        if not school:
            return Response({'error': f'{school_type.capitalize()} school not found.'}, status=status.HTTP_404_NOT_FOUND)
        menus = Menu.objects.filter(
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None,
            cycle_name=cycle_name
        )
        if start_date and end_date:
            menus = menus.filter(start_date__lte=start_date, end_date__gte=end_date)

        if not menus.exists():
            return Response({'error': f'No menus found for {cycle_name} within the specified date range in this school.'}, status=status.HTTP_404_NOT_FOUND)

        menu_data = {}
        for menu in menus:
            menu_data.setdefault(menu.menu_day, []).append({
                'name': menu.name,
                'price': menu.price,
                'category': menu.category.name_category,
                'menu_date': menu.menu_date,
                'cycle_name': menu.cycle_name,
                'is_active': menu.is_active 
            })

        return Response({'status': 'Menus retrieved successfully!', 'menus': menu_data}, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
   
        school_type = request.data.get('school_type') 
        cycle_name = request.data.get('cycle_name')
        start_date = request.data.get('start_date')  
        end_date = request.data.get('end_date')  

       
        if not school_type or not cycle_name:
            return Response({'error': 'Both school_type and cycle_name are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)


        if school_type == 'primary':
            school = PrimarySchool.objects.first()  
        elif school_type == 'secondary':
            school = SecondarySchool.objects.first()
        else:
            return Response({'error': 'Invalid school_type. Use "primary" or "secondary".'}, status=status.HTTP_400_BAD_REQUEST)

        if not school:
            return Response({'error': f'{school_type.capitalize()} school not found.'}, status=status.HTTP_404_NOT_FOUND)

  
        menus_to_delete = Menu.objects.filter(
            primary_school=school if school_type == 'primary' else None,
            secondary_school=school if school_type == 'secondary' else None,
            cycle_name=cycle_name
        )

        if start_date and end_date:
            menus_to_delete = menus_to_delete.filter(start_date__lte=start_date, end_date__gte=end_date)

        if not menus_to_delete.exists():
            return Response({'error': f'No menus found for {cycle_name} within the specified date range in this school.'}, status=status.HTTP_404_NOT_FOUND)

        menus_to_delete.delete()

        return Response({'message': f'All menus for {cycle_name} in the specified school and date range have been deleted.'}, status=status.HTTP_204_NO_CONTENT)

    return Response({'error': 'Invalid request method.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


#
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
    if request.method=='POST':
        serializer=MenuItemsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED, )
        else:
            return Response({ "error" : serializer.errors},status = status.HTTP_400_BAD_REQUEST)


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