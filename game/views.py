from .serializers import InvitationSerializer
from .models import Invitation, Team, TeamMembership, Notification
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .serializers import UserRegistrationSerializer, LoginSerializer, CustomUserSerializer, TeamSerializer, TeamMembershipSerializer, InvitationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from . models import CustomUser, Team, TeamMembership, Invitation, Notification
from .permissions import PersinalPagePermission
from django.db.models import Q, F


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

            user = authenticate(request,  username=username, password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key})
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
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
         

class TeamMembershipViewSet(viewsets.ModelViewSet):
    queryset = TeamMembership.objects.all()
    serializer_class = TeamMembershipSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, PersinalPagePermission]

    # Get information only owner
    def get_queryset(self):
        user = self.request.user
        return CustomUser.objects.filter(username=user)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user

        # Check if the user already has a team as a creator
        if Team.objects.filter(creator=user).exists():
            return Response({"error": "User already has a created team."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the user is an active member of any team
        if TeamMembership.objects.filter(player=user, member_status=True).exists():
            return Response({"error": "User is already an active member of a team."}, status=status.HTTP_400_BAD_REQUEST)

        # Extract team name from the request data
        team_name = request.data.get('name')
        if Team.objects.filter(name=team_name).exists():
            return Response({"error": "A team with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Proceed with standard creation process if checks pass
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user
        team = serializer.save(creator=user)
        # Automatically assign member status to the team creator
        TeamMembership.objects.create(
            team=team, player=user, member_status=True)
        # Initial member count set to 1 as the creator is automatically added
        team.member_count = 1
        team.save()

    def get_queryset(self):
        user = self.request.user
        # Users can view teams they are a part of
        return Team.objects.filter(memberships__player=user)

    def perform_update(self, serializer):
        # Automatically updates the member count on team updates
        serializer.save()
        team = serializer.instance
        team.member_count = team.memberships.filter(member_status=True).count()
        team.save()


# დასატესტია!!!!
# Invitations
class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Invitation.objects.filter(Q(sender=user) | Q(receiver=user))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        team = serializer.validated_data['team']
        receiver = serializer.validated_data['receiver']

        # Validation to ensure sender is not sending an invitation to themselves       
        if receiver == request.user:
            return Response({"error": "You cannot send an invitation to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        if not team.memberships.filter(player=request.user, member_status=True).exists():
            return Response({"error": "You are not authorized to send invitations for this team."}, status=status.HTTP_403_FORBIDDEN)

        if team.memberships.filter(member_status=True).count() >= 7:
            return Response({"error": "Team cannot have more than 7 active members"}, status=status.HTTP_400_BAD_REQUEST)

        if TeamMembership.objects.filter(team=team, player=receiver, member_status=True).exists():
            return Response({"error": "User already has an active membership in the team"}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(sender=request.user)

        Notification.objects.create(
            user=receiver, message="You have received an invitation to join a team.")
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    def partial_update(self, request, *args, **kwargs):
        invitation = self.get_object()

        # Check if the current user is the receiver of the invitation
        if request.user != invitation.receiver:
            return Response({"error": "You do not have permission to update this invitation."},
                            status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        if new_status not in ['Accepted', 'Declined']:
            return Response({"error": "Invalid status. Only 'Accepted' or 'Declined' are allowed."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Prevent updates if the invitation has already been accepted or declined
        if invitation.status in ['Accepted', 'Declined']:
            return Response({"error": "This invitation has already been responded to and cannot be updated."},
                            status=status.HTTP_400_BAD_REQUEST)

        if new_status == 'Accepted':
            # Process acceptance...
            invitation.status = new_status
            invitation.save()
            TeamMembership.objects.update_or_create(
                team=invitation.team,
                player=request.user,
                defaults={'member_status': True})
            # Increment the team's member count appropriately
            invitation.team.member_count += 1
            invitation.team.save()
            Notification.objects.create(
                user=invitation.sender,
                message=f"{request.user.username} has accepted your invitation to join {invitation.team.name}.")
            return Response({'message': 'Invitation accepted and team membership updated.'}, status=status.HTTP_200_OK)

        elif new_status == 'Declined':
            # Process declination...
            invitation.status = new_status
            invitation.save()
            return Response({'message': 'Invitation declined.'}, status=status.HTTP_200_OK)

        # For any other status updates not covered above
        return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)
