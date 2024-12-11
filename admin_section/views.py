from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from .serializers import *
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
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
