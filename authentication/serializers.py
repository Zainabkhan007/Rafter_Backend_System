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

        # Validate password with Django's check_password function
        if user and check_password(password, user.password):  # Use check_password to compare hashed password
            attrs['user'] = user
            attrs['user_type'] = user_type
        else:
            raise serializers.ValidationError("Invalid email or password.")
        
        return attrs
