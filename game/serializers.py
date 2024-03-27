from datetime import timezone
from rest_framework import serializers
from .models import CustomUser, Team, TeamRole, Invitation, Notification, update_team_status, Tournament, Game, GameSchedule
from django.contrib.auth.hashers import make_password
from django.db import transaction

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


# Team / Invitations

class TeamSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    creator_role = serializers.ChoiceField(choices=TeamRole.MAIN_ROLE_CHOICES, write_only=True)

    class Meta:
        model = Team
        fields = ['id', 'creator', 'name', 'logo', 'created_at', 'status', 'member_count', 'members', 'creator_role']
        read_only_fields = ['id', 'created_at', 'status', 'creator', 'member_count', 'members']

    def get_members(self, obj):
        roles = TeamRole.objects.filter(team=obj).select_related('member')
        return [{'member_id': role.member.id, 'in_game_name': role.member.in_game_name, 'role': role.role} for role in roles]
    

class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ['id', 'sender', 'receiver', 'team', 'role', 'status']
        read_only_fields = ['id', 'sender', 'created_at']

    
    def validate(self, attrs):
        super().validate(attrs)
        request = self.context.get('request')
        user = request.user # The current user attempting to create the invitation

        # The team to which the invitation is being sent
        team = attrs.get('team')

        # Check if the current user is the creator of the team
        if request.method == 'POST' and team.creator != user:
            raise serializers.ValidationError({
                "detail": "Only the team creator can send invitations."
            })
        # Only perform certain validations when creating a new invitation

        if request.method == 'POST':
            receiver = attrs.get('receiver')
            team = attrs.get('team')
            role = attrs.get('role')

            # Check if an invitation for the same role in the team is pending or accepted
            existing_invitation = Invitation.objects.filter(
                team=team,
                role=role,
                # Assuming these are the statuses where another invite should be blocked
                status__in=['Pending', 'Accepted']
            ).exists()
            
            if existing_invitation:
                raise serializers.ValidationError(f"An active invitation for the role '{
                                                 role}' in this team already exists.")

            if role in [choice[0] for choice in TeamRole.SUB_ROLE_CHOICES] and not team.status:
                raise serializers.ValidationError(
                    "Invitations for sub roles can only be sent after the team is created.")

            sender = request.user
            if not TeamRole.objects.filter(team=team, member=sender).exists() and team.creator != sender:
                raise serializers.ValidationError(
                    "You must be a member of the team to send invitations.")

            if TeamRole.objects.filter(team=team, role=role).exists():
                raise serializers.ValidationError(
                    f"The role '{role}' already exists in the team.")

        return attrs
    

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


    def update(self, instance, validated_data):
        # Ensure status can only be changed once and by the intended receiver
        user = self.context['request'].user
        if instance.status != 'Pending' or instance.receiver != user:
            raise serializers.ValidationError("You cannot change the invitation status.")

        with transaction.atomic():
            response = super().update(instance, validated_data)

            # Create a notification for the sender when the receiver responds
            Notification.objects.create(
                user=instance.sender,
                message=f"{user.full_name} has {'accepted' if instance.status == 'Accepted' else 'declined'} your invitation to join the team {instance.team.name}."
            )

            # If the invitation is accepted, add the user to the team roles
            if instance.status == 'Accepted':
                team_role, created = TeamRole.objects.get_or_create(
                    team=instance.team,
                    member=user,
                    defaults={'role': instance.role}
                )

                # Update team status if necessary, similar logic as in the signal
                update_team_status(sender=TeamRole, instance=team_role, created=created, team=instance.team)

            return instance


# Teams list
class TeamsListSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    creator_role = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'creator', 'name', 'logo', 'created_at', 'status', 'member_count', 'members', 'creator_role']

    def get_members(self, obj):
        # Retrieve all TeamRole instances related to the team
        team_roles = TeamRole.objects.filter(team=obj)
        # Serialize each TeamRole into a simple dictionary
        members_list = [{
            'member_id': team_role.member.id,
            'in_game_name': team_role.member.in_game_name,
            'role': team_role.role
        } for team_role in team_roles]
        return members_list

    def get_creator_role(self, obj):
        # Example logic to determine the creator's role
        creator_role = TeamRole.objects.filter(team=obj, member=obj.creator).first()
        return creator_role.role if creator_role else None


# Users list
class UsersListSerializer(serializers.ModelSerializer):
    teams_roles = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ["id", "username", "full_name", "in_game_name", "teams_roles"]

    def get_teams_roles(self, obj):
        # Fetch all TeamRole instances related to the user
        team_roles = TeamRole.objects.filter(member=obj)
        # Serialize the TeamRole information into a list of dictionaries
        return [{
            'team_id': team_role.team.id,
            'team_name': team_role.team.name,
            'role': team_role.role
        } for team_role in team_roles]



# Notifications
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def __init__(self, *args, **kwargs):
        super(NotificationSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if not request or not request.user.is_staff:
            self.fields['message'].read_only = True



# Tournaments
class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = "__all__"
        read_only_fields = ['teams']

    def create(self, validated_data):
        # Logic to check start_time and end_time constraints
        if not (Tournament.start_time <= timezone.now() <= Tournament.end_time):
            raise serializers.ValidationError("Registration is not open.")
        return super().create(validated_data)
    

# Games 
class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"
        read_only_fields = ['tournament', 'team', 'score', 'win', 'lost', 'total_game', 'registered_time']



# Game schedule
class GameScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSchedule
        fields = "__all__"
        read_only_fields = ['tournament', 'time', 'team_1', 'team_2', 'score_team_1', 'score_team_2', 'vote']

    def update(self, instance, validated_data):
        user = self.context['request'].user
        # Logic for image upload and score update
        if 'image_team_1' in validated_data:
            if instance.team_1.creator != user:
                raise serializers.ValidationError("Only the team creator can upload an image for team 1.")
            instance.score_team_1 += 1
            instance.team_1.score += 1  # Assuming 'score' is a field on Team model
        # Similar logic for team_2
        return super().update(instance, validated_data)
