from django.utils import timezone
from rest_framework import serializers
from .models import CustomUser, Team, TeamRole, Invitation, Notification, update_team_status, Tournament, TournamentRegistration, Game, GameSchedule
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

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
                raise serializers.ValidationError(f"An active invitation for the role '{role}' in this team already exists.")
            
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

    def validate(self, data):
        if self.context['request'].user.is_admin:
            return data
        raise PermissionDenied("Only admin users can create tournaments.")

    def create(self, validated_data):
        if self.context['request'].user.is_admin:
            return super().create(validated_data)
        raise PermissionDenied("Only admin users can create tournaments.")


# Tournament registration
class TournamentRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentRegistration
        fields = "__all__"

    def validate(self, data):
        team = data['team']
        tournament = data['tournament']
        if not team.creator == self.context['request'].user:
            raise PermissionDenied("Only team creators can register the team.")
        if not team.status:
            raise serializers.ValidationError("Team is not complete.")
        if not tournament.start_time <= timezone.now() <= tournament.end_time:
            raise serializers.ValidationError("Registration is not open.")
        if TournamentRegistration.objects.filter(team=team, tournament=tournament).exists():
            raise serializers.ValidationError("Team is already registered for this tournament.")
        return data


# Game Schedule
class GameScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSchedule
        fields = "__all__"
        read_only_fields = ['tournament', 'time', 'team_1', 'team_2', 'score_team_1', 'score_team_2', 'vote_updated_by']

    def update_vote(self, instance, validated_data):
        user = self.context['request'].user
        if 'vote' in validated_data:
            if user in instance.vote_updated_by.all():
                raise serializers.ValidationError("You have already voted for this game.")
            instance.vote_updated_by.add(user)
            instance.vote = validated_data['vote']  # Update the vote field directly
            instance.save()
        return instance

    def update_image(self, instance, validated_data):
        user = self.context['request'].user
        current_time = timezone.now()
        game_time = instance.time
        time_difference = current_time - game_time

        if time_difference.total_seconds() > 172800:  # 48 hours = 172800 seconds
            raise serializers.ValidationError("Score and image can only be updated within 48 hours after the game began.")

        if 'image_team_1' in validated_data:
            if instance.team_1.creator != user:
                raise serializers.ValidationError("Only the team creator can upload an image.")
            instance.score_team_1 += 1
            game_1 = GameSchedule.objects.get(team_1=instance.team_1, tournament=instance.tournament)
            game_1.score_team_1 += 1
            game_1.save()

        if 'image_team_2' in validated_data:
            if instance.team_2.creator != user:
                raise serializers.ValidationError("Only the team creator can upload an image.")
            instance.score_team_2 += 1
            game_2 = GameSchedule.objects.get(team_2=instance.team_2, tournament=instance.tournament)
            game_2.score_team_2 += 1
            game_2.save()

        return super().update(instance, validated_data)


# Game History
class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"
        read_only_fields = ['tournament', 'team', 'score', 'win', 'lost', 'total_game', 'registered_time']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        current_time = timezone.now()
        game_schedules = GameSchedule.objects.filter(
            tournament=instance.tournament, team_1=instance.team).order_by('time')
        for schedule in game_schedules:

            game_time = schedule.time
            time_difference = current_time - game_time
            if time_difference.total_seconds() > 172800 and not schedule.winner_updated:
                if schedule.score_team_1 > schedule.score_team_2:
                    instance.win += 1
                elif schedule.score_team_1 < schedule.score_team_2:
                    game_2 = Game.objects.get(team=schedule.team_2, tournament=schedule.tournament)
                    game_2.win += 1
                    game_2.save()
                schedule.winner_updated = True
                schedule.save()
        instance.save()
        return representation
