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
        fields = ['id','first_name', 'last_name', 'username', 'email','phone_no','allergies','credits','password']
        def update(self, instance, validated_data):
       
         if 'password' not in validated_data:
            validated_data['password'] = instance.password 

         return super().update(instance, validated_data)
        

class StaffRegisterationSerializer(serializers.ModelSerializer):
    
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)
    class Meta:
        model = StaffRegisteration
        fields = ['id','first_name', 'last_name', 'username', 'email','phone_no',"allergies",'credits','password','primary_school','secondary_school']
    def update(self, instance, validated_data):
       
        if 'password' not in validated_data:
            validated_data['password'] = instance.password 

        return super().update(instance, validated_data)
    def create(self, validated_data):

        school_type = validated_data.get('school_type')  
        school_id = validated_data.get('school_id')  

        if school_type == "primary":
            validated_data['primary_school'] = PrimarySchool.objects.get(id=school_id)
        elif school_type == "secondary":
            validated_data['secondary_school'] = SecondarySchool.objects.get(id=school_id)
        else:
            raise serializers.ValidationError({"school_type": "Invalid school type provided. Use 'primary' or 'secondary'."})

        return super().create(validated_data)

class CanteenStaffSerializer(serializers.ModelSerializer):
    school_type = serializers.ChoiceField(choices=[('primary', 'Primary'), ('secondary', 'Secondary')])
    primary_school = serializers.PrimaryKeyRelatedField(queryset=PrimarySchool.objects.all(), required=False)
    secondary_school = serializers.PrimaryKeyRelatedField(queryset=SecondarySchool.objects.all(), required=False)
    school_name = serializers.SerializerMethodField()  

    class Meta:
        model = CanteenStaff
        fields = ['id', 'username', 'email', 'password', 'school_type', 'primary_school', 'secondary_school', 'school_name']

    def get_school_name(self, obj):
        if obj.school_type == 'primary' and obj.primary_school:
            return obj.primary_school.school_name
        elif obj.school_type == 'secondary' and obj.secondary_school:
            return obj.secondary_school.secondary_school_name
        return 'Unknown School'

    def update(self, instance, validated_data):
        # Prevent password from being overwritten unless explicitly provided
        if 'password' not in validated_data:
            validated_data['password'] = instance.password
        return super().update(instance, validated_data)
class ManagerSerializer(serializers.ModelSerializer):
    school_name = serializers.SerializerMethodField()

    class Meta:
        model = Manager
        fields = [
            'id',
            'username',
            'password',
            'school_type',
            'primary_school',
            'secondary_school',
            'school_name',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def get_school_name(self, obj):
        if obj.school_type == 'primary' and obj.primary_school:
            return obj.primary_school.school_name
        elif obj.school_type == 'secondary' and obj.secondary_school:
            return obj.secondary_school.secondary_school_name
        return 'Unknown School'

class ManagerOrderItemSerializer(serializers.ModelSerializer):
    menu_item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItems.objects.all(),
        source='menu_item',
        write_only=True,
        required=False,
    )
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)

    class Meta:
        model = ManagerOrderItem
        fields = [
            'id',
            'day',
            'item',
            'quantity',
            'remarks',
            'menu_item_id',  
            'menu_item_name',  
        ]


class ManagerOrderSerializer(serializers.ModelSerializer):
    items = ManagerOrderItemSerializer(many=True)
    manager = serializers.PrimaryKeyRelatedField(queryset=Manager.objects.all())

    class Meta:
        model = ManagerOrder
        fields = [
            'id',
            'manager',
            'order_date',
            'week_number',
            'year',
            'status',
            'selected_day',
            'is_delivered',
            'items',
            'total_production_price',
        ]
        read_only_fields = ['order_date', 'total_production_price']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = ManagerOrder.objects.create(**validated_data)

        for item_data in items_data:
            menu_item = item_data.get('menu_item', None)
            ManagerOrderItem.objects.create(order=order, **item_data)

        return order


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    
    def validate(self, attrs):
        email = attrs.get('email').strip().lower()  
        password = attrs.get('password')
        
        user = None
        user_type = None
        
        # Case-insensitive lookups
        try:
            user = StaffRegisteration.objects.get(email__iexact=email)
            user_type = 'staff'
        except StaffRegisteration.DoesNotExist:
            pass

        if not user:
            try:
                user = ParentRegisteration.objects.get(email__iexact=email)
                user_type = 'parent'
            except ParentRegisteration.DoesNotExist:
                pass

        if not user:
            try:
                user = SecondaryStudent.objects.get(email__iexact=email)
                user_type = 'student'
            except SecondaryStudent.DoesNotExist:
                pass

        if not user:
            try:
                user = CanteenStaff.objects.get(email__iexact=email)
                user_type = 'canteenstaff'
            except CanteenStaff.DoesNotExist:
                pass

        # Check password
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
    school_name = serializers.CharField(source='school.school_name', read_only=True)

    class Meta:
        model = Teacher
        fields = ['id', 'teacher_name', 'class_year', 'school_name']



class SecondaryStudentSerializer(serializers.ModelSerializer):
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)
    school_name = serializers.CharField(source='school.name', read_only=True)
    school = serializers.PrimaryKeyRelatedField(queryset=SecondarySchool.objects.all()) 
    class Meta:
        model = SecondaryStudent
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone_no', 'class_year', 'school_name','school' , 'allergies','credits','password']
    def update(self, instance, validated_data):
       
         if 'password' not in validated_data:
            validated_data['password'] = instance.password 

        
         return super().update(instance, validated_data)

class TopUpCreditsSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, required=True)
    user_id = serializers.IntegerField(required=True)  
    user_type = serializers.ChoiceField(choices=["parent", "staff", "student"], required=True)   
    
class StaffRegisterationSerializer(serializers.ModelSerializer):
    allergies = serializers.SlugRelatedField(queryset=Allergens.objects.all(), slug_field='allergy', many=True, required=False)
    
   
    school_name = serializers.CharField(source='get_school_name', read_only=True)
    primary_school = serializers.PrimaryKeyRelatedField(queryset=PrimarySchool.objects.all(), required=False)
    secondary_school = serializers.PrimaryKeyRelatedField(queryset=SecondarySchool.objects.all(), required=False)
    
    class Meta:
        model = StaffRegisteration
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone_no', 'allergies','credits', 'password', 'primary_school', 'secondary_school', 'school_name']
    def update(self, instance, validated_data):
       
         if 'password' not in validated_data:
            validated_data['password'] = instance.password 

         return super().update(instance, validated_data)
  

class SecondarySchoolSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = SecondarySchool
        fields =  ['id', 'secondary_school_name', 'secondary_school_email', 'secondary_school_eircode', 'student_count']

class PrimaryStudentSerializer(serializers.ModelSerializer):
    allergies = serializers.SlugRelatedField(
        queryset=Allergens.objects.all(),
        slug_field='allergy',
        many=True,
        required=False
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=ParentRegisteration.objects.all(),
        required=False
    )
    staff = serializers.PrimaryKeyRelatedField(
        queryset=StaffRegisteration.objects.all(),
        required=False
    )

    teacher_id = serializers.IntegerField(source='teacher.id', read_only=True)
    teacher_name = serializers.CharField(source='teacher.teacher_name', read_only=True)

    class Meta:
        model = PrimaryStudentsRegister
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'class_year',
            'teacher',        
            'teacher_id',
            'teacher_name',  
            'school',
            'allergies',
            'parent',
            'staff'
        ]

class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields =  fields =  ['id', 'name_category', 'emoji', 'image']



class MenuSerializer(serializers.ModelSerializer):

    
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
    allergies = serializers.SlugRelatedField(
        queryset=Allergens.objects.all(),
        slug_field='allergy',
        many=True,
        required=False
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuItems
        fields = [
            'id',
            'item_name',
            'item_description',
            'ingredients',
            'nutrients',
            'allergies',
            'image',
            'image_url',
            'production_price',
            'is_available', 
        ]
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def validate(self, data):
        # Ensure image is optional
        if 'image' in data and not data['image']:
            data['image'] = None
        return data


class OrderItemSerializer(serializers.ModelSerializer):
    # This correctly gets the menu name from the related Menu object
    item_name = serializers.CharField(source='menu.name', read_only=True)
    menu = MenuSerializer(read_only=True)  # This will serialize the full menu object

    class Meta:
        model = OrderItem
        fields = ['id', 'menu', 'item_name', 'quantity', 'order']

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True, source='order_items')
    user_name = serializers.SerializerMethodField()
    child_id = serializers.IntegerField(required=False, allow_null=True)
    
    week_number = serializers.IntegerField(default=datetime.now().isocalendar()[1], read_only=False)
    year = serializers.IntegerField(default=datetime.now().year, read_only=False)

    class Meta:
        model = Order
        # ✅ Removed 'items_name' from the fields list
        fields = [
            'items', 'user_name', 'child_id', 'week_number', 'year',
            'order_date', 'selected_day', 'is_delivered', 'status',
            'payment_id', 'primary_school', 'secondary_school',
            'total_price', 'user_type', 'user_id'
        ]
  
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


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['full_name', 'email', 'phone', 'subject', 'message', 'photo_filename']

class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = ["platform", "latest_version", "min_supported_version", "force_update"]
