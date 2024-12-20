from .models import *
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password 
from django.contrib.auth.tokens import default_token_generator


class ParentRegisterationSerializer(serializers.ModelSerializer):
   
   
    class Meta:
        model = ParentRegisteration
        fields = "__all__"
        
class StudentRegisterationSerializer(serializers.ModelSerializer):
   
   
    class Meta:
        model = StudentRegisteration
        fields = "__all__"

class StaffRegisterationSerializer(serializers.ModelSerializer):
   
   
    class Meta:
        model = StaffRegisteration
        fields = "__all__"


class CanteenStaffSerializer(serializers.ModelSerializer):
    school_type = serializers.ChoiceField(choices=[('primary', 'Primary'), ('secondary', 'Secondary')])

    class Meta:
        model = CanteenStaff
        fields = ['username', 'email', 'password', 'school_type']  # Removed school_id from fields

    def validate(self, data):
        school_type = data.get('school_type')

        # Get school_id from context
        school_id = self.context.get('school_id')

        # Validate based on school_type
        if school_type == 'primary':
            if not PrimarySchool.objects.filter(id=school_id).exists():
                raise serializers.ValidationError("Primary school with the provided ID does not exist.")
            # Assign the primary school
            data['primary_school'] = PrimarySchool.objects.get(id=school_id)
            data['secondary_school'] = None  # Ensure secondary_school is not set

        elif school_type == 'secondary':
            if not SecondarySchool.objects.filter(id=school_id).exists():
                raise serializers.ValidationError("Secondary school with the provided ID does not exist.")
            # Assign the secondary school
            data['secondary_school'] = SecondarySchool.objects.get(id=school_id)
            data['primary_school'] = None  # Ensure primary_school is not set

        else:
            raise serializers.ValidationError("Invalid school type.")

        return data
 
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        user = None
        user_type = None
       
        try:
            user = StaffRegisteration.objects.get(email=email)
            user_type = 'staff'
        except StaffRegisteration.DoesNotExist:
            pass

        if not user:
            try:
                user = ParentRegisteration.objects.get(email=email)
                user_type = 'parent'
            except ParentRegisteration.DoesNotExist:
                pass

        if not user:
            try:
                user = StudentRegisteration.objects.get(email=email)
                user_type = 'student'
            except StudentRegisteration.DoesNotExist:
                pass
        if not user:
            try:
                user = CanteenStaff.objects.get(email=email)
                user_type = 'canteenstaff'
            except StudentRegisteration.DoesNotExist:
                pass
        # Validate password with Django's check_password function
        if user and check_password(password, user.password):  # Use check_password to compare hashed password
            attrs['user'] = user
            attrs['user_type'] = user_type
        else:
            raise serializers.ValidationError("Invalid email or password.")
        
        return attrs

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
class AllergenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergen
        fields = ['id', 'allergy']

class MenuItemsSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(queryset=Categories.objects.all(), slug_field='name_category')
    allergies=serializers.SlugRelatedField(queryset=Allergen.objects.all(), slug_field='allergy')
    class Meta:
        model = MenuItems
        fields = ['id','category', 'item_name', 'item_description', 'nutrients', 'ingredients','allergies']

class OrderItemSerializer(serializers.ModelSerializer):
    menu = MenuSerializer() 
    quantity = serializers.IntegerField()  

    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()  # Add user_name field
    child_id = serializers.IntegerField(required=False, allow_null=True)  # Add child_id for parents and staff

    week_number = serializers.IntegerField(default=datetime.now().isocalendar()[1], read_only=False)
    year = serializers.IntegerField(default=datetime.now().year, read_only=False)

    class Meta:
        model = Order
        fields = '__all__'  # Including all fields for the Order model

    def get_user_name(self, obj):
        """Return the user name based on the user type."""
        return obj.get_user_name()  # Call the method in the model to get the user name

    def to_representation(self, instance):
        """Customize the serialization."""
        representation = super().to_representation(instance)
        
        # For parents and staff, include child_id and exclude child_name
        if instance.user_type in ['parent', 'staff']:
            representation['child_id'] = instance.child_id
            representation.pop('child_name', None)  # Remove child_name for parents and staff
        else:
            representation.pop('child_id', None)  # Remove child_id for students
        
        return representation

