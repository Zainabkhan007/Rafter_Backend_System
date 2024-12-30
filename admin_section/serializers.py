from .models import *
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password 
from django.contrib.auth.tokens import default_token_generator

class AllergenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergens
        fields = ['id', 'allergy']
class ParentRegisterationSerializer(serializers.ModelSerializer):
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)
   
    class Meta:
        model = ParentRegisteration
        fields = ['id','first_name', 'last_name', 'username', 'email','phone_no','allergies','password']
        

class StaffRegisterationSerializer(serializers.ModelSerializer):
    
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)
    class Meta:
        model = StaffRegisteration
        fields = ['id','first_name', 'last_name', 'username', 'email','phone_no',"allergies",'password','primary_school','secondary_school']
    def create(self, validated_data):
       
        # Handle school assignment based on school_type
        school_type = validated_data.get('school_type')  # school_type from the validated data
        school_id = validated_data.get('school_id')  # school_id from the validated data

        if school_type == "primary":
            validated_data['primary_school'] = PrimarySchool.objects.get(id=school_id)
        elif school_type == "secondary":
            validated_data['secondary_school'] = SecondarySchool.objects.get(id=school_id)
        else:
            raise serializers.ValidationError({"school_type": "Invalid school type provided. Use 'primary' or 'secondary'."})

        return super().create(validated_data)

class CanteenStaffSerializer(serializers.ModelSerializer):
    school_type = serializers.ChoiceField(choices=[('primary', 'Primary'), ('secondary', 'Secondary')])

    class Meta:
        model = CanteenStaff
        fields = ['username', 'email', 'password', 'school_type']  # Removed school_id from fields

    def validate(self, data):
        school_type = data.get('school_type')

        
        school_id = self.context.get('school_id')

        
        if school_type == 'primary':
            if not PrimarySchool.objects.filter(id=school_id).exists():
                raise serializers.ValidationError("Primary school with the provided ID does not exist.")
            
            data['primary_school'] = PrimarySchool.objects.get(id=school_id)
            data['secondary_school'] = None  

        elif school_type == 'secondary':
            if not SecondarySchool.objects.filter(id=school_id).exists():
                raise serializers.ValidationError("Secondary school with the provided ID does not exist.")
          
            data['secondary_school'] = SecondarySchool.objects.get(id=school_id)
            data['primary_school'] = None  

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
                user = SecondaryStudent.objects.get(email=email)
                user_type = 'student'
            except SecondaryStudent.DoesNotExist:
                pass
        if not user:
            try:
                user = CanteenStaff.objects.get(email=email)
                user_type = 'canteenstaff'
            except CanteenStaff.DoesNotExist:
                pass
       
        if user and check_password(password, user.password):  
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
        fields = ['id','teacher_name', 'class_year']



class SecondaryStudentSerializer(serializers.ModelSerializer):
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)
    school_name = serializers.CharField(source='school.name', read_only=True)
    school = serializers.PrimaryKeyRelatedField(queryset=SecondarySchool.objects.all()) 
    class Meta:
        model = SecondaryStudent
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone_no', 'class_year', 'school_name','school' , 'allergies','password']
   
class StaffRegisterationSerializer(serializers.ModelSerializer):
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)
    
    # School fields: will return the appropriate school based on type (primary or secondary)
    school_name = serializers.CharField(source='get_school_name', read_only=True)
    primary_school = serializers.PrimaryKeyRelatedField(queryset=PrimarySchool.objects.all(), required=False)
    secondary_school = serializers.PrimaryKeyRelatedField(queryset=SecondarySchool.objects.all(), required=False)
    
    class Meta:
        model = StaffRegisteration
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone_no', 'allergies', 'password', 'primary_school', 'secondary_school', 'school_name']

  

class SecondarySchoolSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = SecondarySchool
        fields =  ['id', 'secondary_school_name', 'secondary_school_email', 'secondary_school_eircode', 'student_count']


class PrimaryStudentSerializer(serializers.ModelSerializer):
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)
    parent = serializers.PrimaryKeyRelatedField(queryset=ParentRegisteration.objects.all(), required=False)
    staff = serializers.PrimaryKeyRelatedField(queryset=StaffRegisteration.objects.all(), required=False)
    
    class Meta:
        model = PrimaryStudentsRegister
        fields =['id', 'first_name', 'last_name',  'class_year', 'teacher','school' , 'allergies','parent','staff']


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields =  fields =  ['id', 'name_category', 'emoji', 'image']



class MenuSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    
    primary_school_name = serializers.CharField(source='primary_school.school_name', read_only=True, required=False, allow_null=True)
    secondary_school_name = serializers.CharField(source='secondary_school.school_name', read_only=True, required=False, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Categories.objects.all())
    primary_school_id = serializers.PrimaryKeyRelatedField(source='primary_school.id', read_only=True)
    secondary_school_id = serializers.PrimaryKeyRelatedField(source='secondary_school.id', read_only=True)
    
    class Meta:
        model = Menu
        fields = ['id', 'name', 'price', 'menu_day', 'cycle_name', 'menu_date', 'primary_school_name', 
                  'secondary_school_name', 'category', 'is_active', 'primary_school_id', 'secondary_school_id']

    def to_representation(self, instance):
        """ Customize the representation to include more details """
        representation = super().to_representation(instance)
            
        representation['category'] = instance.category.name_category if instance.category else None
        return representation



class MenuItemsSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(queryset=Categories.objects.all(), slug_field='name_category')
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)

    class Meta:
        model = MenuItems
        fields = ['id','category', 'item_name', 'item_description', 'nutrients', 'ingredients','allergies']

class OrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='menu.name', read_only=True)
    menu = MenuSerializer() 
    quantity = serializers.IntegerField()  

    class Meta:
        model = OrderItem
        fields = ['id','menu','item_name', 'quantity', 'order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()  
    child_id = serializers.IntegerField(required=False, allow_null=True)  

    week_number = serializers.IntegerField(default=datetime.now().isocalendar()[1], read_only=False)
    year = serializers.IntegerField(default=datetime.now().year, read_only=False)

    class Meta:
        model = Order
        fields = '__all__'  

    def get_user_name(self, obj):
        """Return the user name based on the user type."""
        return obj.get_user_name()  

    def to_representation(self, instance):
        """Customize the serialization."""
        representation = super().to_representation(instance)
        
       
        if instance.user_type in ['parent', 'staff']:
            representation['child_id'] = instance.child_id
            representation.pop('child_name', None) 
        else:

            representation.pop('child_id', None)  
        
        return representation

