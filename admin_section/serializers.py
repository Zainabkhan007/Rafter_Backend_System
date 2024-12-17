from .models import *
from rest_framework import serializers

class PrimarySchoolSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = PrimarySchool
        fields =  ['id', 'school_name', 'school_email', 'school_eircode', 'student_count']


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['teacher_name', 'class_year']

class StudentSerializer(serializers.ModelSerializer):
    # Define a custom field to get the teacher's name
    teacher_name = serializers.CharField(source='teacher.teacher_name')  
    
    class Meta:
        model = Student
        fields = ['student_name', 'class_year', 'teacher_name', 'student_email']


class SecondarySchoolSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = SecondarySchool
        fields =  ['id', 'secondary_school_name', 'secondary_school_email', 'secondary_school_eircode', 'student_count']


class SecondaryStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecondaryStudent
        fields = ['secondary_student_name', 'secondary_class_year','secondary_school','seconadry_student_email', ]


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = '__all__'


    
class MenuSerializer(serializers.ModelSerializer):
    # Ensure that we display the is_active field
    is_active = serializers.BooleanField(read_only=True)  # Computed from is_active_time
    
    primary_school = serializers.PrimaryKeyRelatedField(queryset=PrimarySchool.objects.all(), required=False, allow_null=True)
    secondary_school = serializers.PrimaryKeyRelatedField(queryset=SecondarySchool.objects.all(), required=False, allow_null=True)  # Make this optional
    category = serializers.PrimaryKeyRelatedField(queryset=Categories.objects.all())  # Correct reference to Categories

    class Meta:
        model = Menu
        fields = ['id', 'name', 'price', 'menu_day', 'cycle_name', 'menu_date', 'primary_school', 'secondary_school', 'category', 'is_active']

    def to_representation(self, instance):
        """ Customize the representation to include more details """
        representation = super().to_representation(instance)
        # Accessing 'name_category' in Categories model
        representation['category'] = instance.category.name_category if instance.category else None
        return representation

class MenuItemsSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(queryset=Categories.objects.all(), slug_field='name_category')
    class Meta:
        model = MenuItems
        fields = ['category', 'item_name', 'item_description', 'nutrients', 'ingredients']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'