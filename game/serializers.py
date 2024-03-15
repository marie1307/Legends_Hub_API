from .models import CustomUser, Team, TeamMembership
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Team, TeamMembership, Invitation

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

    
# CustomUser - add full_name and in_game_name / username as email
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'full_name', 'in_game_name')  
        read_only_fields = ('id', 'username', 'full_name')


# Teams / Membership / Invitations

class TeamSerializer(serializers.ModelSerializer):
    creator = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all()) #????? json format or pk?

    class Meta:
        model = Team
        fields = ('id', 'name', 'creator', 'member_count')
        read_only_fields = ('member_count',)

# Team_membership
class TeamMembershipSerializer(serializers.ModelSerializer):
    player = CustomUserSerializer(many=False, read_only=True)
    team = TeamSerializer(many=True, read_only=True)

    class Meta:
        model = TeamMembership
        fields = ('player', 'team', 'member_status')

# Invitation
class InvitationSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    receiver = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = Invitation
        fields = ('sender', 'team', 'receiver', 'role', 'status')
        
