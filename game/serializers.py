from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser

# Registration
# User registration by email, first_name, last_name, in_game_name and password
class UserRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'full_name', 'password', 'in_game_name']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])

        user = CustomUser.objects.create(**validated_data)
        return user


#login 
class LoginSerializer(serializers.Serializer):
    username = serializers.EmailField() #requires authentication with email
    password = serializers.CharField()
