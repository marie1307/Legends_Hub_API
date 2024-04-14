from .serializers import UserRegistrationSerializer, LoginSerializer, CustomUserSerializer, TeamSerializer, InvitationSerializer, NotificationSerializer, TeamsListSerializer, UsersListSerializer, TournamentSerializer, TournamentRegistrationSerializer, GameSerializer, GameScheduleSerializer
from . models import CustomUser, Team, Invitation, Notification, TeamRole, Tournament, TournamentRegistration, Game, GameSchedule
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from .permissions import PersinalPagePermission, IsTeamCreatorOrReadOnly
from django.db.models import Q, F
from django.db import transaction
from django.core.exceptions import ValidationError as DRFValidationError, PermissionDenied
from rest_framework.exceptions import MethodNotAllowed
from django.utils import timezone


# Registration
class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if CustomUser.objects.filter(username=request.data["username"]).exists():
            return Response({"status": "User with this username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': serializer.data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Login
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            # Checks if a user with the provided username exists
            user_exists = CustomUser.objects.filter(username=username).exists()
            if not user_exists:
                # If the user doesn't exist, returns error message
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # authenticates the user
            user = authenticate(request,  username=username, password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                update_last_login(None, user)
                user_serializer = CustomUserSerializer(user)
                # returns user information including token, username, in_game_name and Full_name
                response_data = {
                    'token': token.key,
                    # 'username': user_serializer.data['username'],
                    # 'in_game_name': user_serializer.data['in_game_name'],
                    # 'full_name': user_serializer.data['full_name'], 
                }
                return Response(response_data)
            else:
                # If authentication fails but the user exists because password is incorrect
                return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Logout
class LogoutAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = Token.objects.get(user=request.user)
        except Token.DoesNotExist:
            return Response({'error': 'No token found for the user'}, status=status.HTTP_400_BAD_REQUEST)

        token.delete()
        return Response({'message': 'User logged out successfully'}, status=status.HTTP_200_OK)


# Teams / Membership / Invitation
    # Personal page details
class CustomUserPersonalPageViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes=[PersinalPagePermission]

    # Get information only owner
    def get_queryset(self):
        user = self.request.user
        return CustomUser.objects.filter(username=user)

    # Updates password only
    def update(self, request, *args, **kwargs):
        user = self.request.user
        if 'password' in request.data:
            password = request.data['password']
            user.set_password(password)
            user.save()
            return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
        elif 'in_game_name' in request.data:
            in_game_name = request.data['in_game_name']
            user.in_game_name = in_game_name
            user.save()
            return Response({'message': 'In-game name updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)
        

# Teams
class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsTeamCreatorOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        user = self.request.user
        if Team.objects.filter(Q(creator=user) | Q(roles__member=user)).exists():
            raise PermissionDenied('You are already a member or creator of a team.')
        
        creator_role = serializer.validated_data.pop('creator_role', None)
        # Save the Team instance with the creator set to the current user
        team = serializer.save(creator=user)

        if creator_role:
            TeamRole.objects.create(team=team, member=user, role=creator_role)
        else:
            # Handle the case where creator_role might be None or not provided properly
            raise DRFValidationError({"detail": "A valid creator_role must be provided."})


    def get_queryset(self):
        # Users can view teams they've created or are a part of
        return Team.objects.filter(Q(creator=self.request.user) | Q(roles__member=self.request.user)).distinct()
    

# Invitations
class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Invitation.objects.filter(Q(sender=user) | Q(receiver=user))

    def perform_create(self, serializer):
        with transaction.atomic():
            user = self.request.user
            receiver = serializer.validated_data['receiver']
            team = serializer.validated_data['team']

            if receiver == user:
                raise DRFValidationError("You cannot invite yourself.")

            if not TeamRole.objects.filter(team=team, member=user).exists() and team.creator != user:
                raise DRFValidationError(
                    "You must be a member of the team to send invitations.")

            if Invitation.objects.filter(receiver=receiver, team=team, status='Pending').exists():
                raise DRFValidationError(
                    "An invitation already exists for this user and team.")

            if TeamRole.objects.filter(member=receiver, team=team).exists():
                raise DRFValidationError(
                    "The invited user is already part of this team.")

            serializer.save(sender=user)

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.instance
            user = self.request.user

            if user != instance.receiver:
                raise PermissionDenied(
                    "Only the receiver of this invitation can update it.")

            new_status = serializer.validated_data.get('status')

            if instance.status != 'Pending':
                raise DRFValidationError(
                    "You can't change the invitation status after a decision has been made.")
            
            if new_status not in ['Accepted', 'Declined']:
                raise DRFValidationError("Invalid status update.")
            
            if TeamRole.objects.filter(member=user).exists():
                raise DRFValidationError(
                    "The invited user is already part of another team.")
            
            serializer.save()

            if new_status == 'Accepted':
                role, created = TeamRole.objects.get_or_create(
                    team=instance.team, member=user, defaults={'role': instance.role})
                if created:
                    self._update_team_status(instance.team)
                    Notification.objects.create(
                        user=instance.sender,
                        message=f"{user.get_full_name()} has accepted your invitation to join the team '{
                            instance.team.name}' as '{instance.role}'."
                    )
            elif new_status == 'Declined':
                Notification.objects.create(
                    user=instance.sender,
                    message=f"{user.get_full_name()} has declined your invitation to join the team '{
                        instance.team.name}' as '{instance.role}'."
                )

    def _update_team_status(self, team):
        main_roles_count = TeamRole.objects.filter(
            team=team,
            role__in=[role[0] for role in TeamRole.MAIN_ROLE_CHOICES]
        ).count()
        if main_roles_count == len(TeamRole.MAIN_ROLE_CHOICES):
            team.status = True
            team.save()

# Teams list
class TeamsListViewSet(viewsets.ReadOnlyModelViewSet):
 
    queryset = Team.objects.all()
    serializer_class = TeamsListSerializer


# Users list
class UsersListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all().prefetch_related('team_roles__team')
    serializer_class = UsersListSerializer


# Notifications
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_staff:
            return Response({"error": "Only admin users can send notifications."}, status=status.HTTP_403_FORBIDDEN)
        
        # Extract notification data from request
        data = request.data

        # Fetch all users except the admin sending the notification
        users = CustomUser.objects.exclude(id=user.id)

        notifications = []
        for user in users:
            # Update the 'user' field in the notification data for each user
            data['user'] = user.id
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                notifications.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(notifications, status=status.HTTP_201_CREATED)



# Tournament
class TournamentViewSet(viewsets.ModelViewSet):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer


class TournamentRegistrationViewSet(viewsets.ModelViewSet):
    queryset = TournamentRegistration.objects.all()
    serializer_class = TournamentRegistrationSerializer
    permission_classes = [IsAuthenticated]


    def retrieve(self, request, *args, **kwargs):
        raise MethodNotAllowed("GET")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT")

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH")

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE")
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tournament = serializer.validated_data['tournament']

        if not tournament.start_time <= timezone.now() <= tournament.end_time:
            raise PermissionDenied(
                "Registration is not open for this tournament.")

        team = Team.objects.filter(creator=request.user).first()
        if not team:
            raise PermissionDenied("You haven't created any team yet.")

        if not team.status:
            raise PermissionDenied("The team is not complete.")

        existing_registration = TournamentRegistration.objects.filter(
            team=team, tournament=tournament).exists()
        if existing_registration:
            raise PermissionDenied("The team is already registered for this tournament.")

        serializer.save(team=team)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

# Game hostory
class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

# Game schedule
class GameScheduleViewSet(viewsets.ModelViewSet):
    queryset = GameSchedule.objects.all()
    serializer_class = GameScheduleSerializer

    def get_permissions(self):
        # Custom permission logic for PATCH requests
        return super().get_permissions()

    # Additional methods for image upload and voting
