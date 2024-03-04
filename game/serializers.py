from rest_framework import serializers
from .models import CustomUser

#registration
# User registration by username (email), first_name, last_name, in_game_name and password
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField()

    class Meta:
        model = CustomUser
        fields = ['username', 'full_name', 'password', 'in_game_name']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user


#login 
class LoginSerializer(serializers.Serializer):
    username = serializers.EmailField() #requires authentication with email
    password = serializers.CharField()
