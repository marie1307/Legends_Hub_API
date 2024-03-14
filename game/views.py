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
from django.db.models import Q


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

    def perform_create(self, serializer):
        # Retrieve the creator instance based on the provided ID
        creator_id = self.request.data.get('creator', {}).get('id')
        creator = get_object_or_404(CustomUser, pk=creator_id)

        # Set the creator for the team
        team = serializer.save(creator=creator)
        
        # Automatically assign member status to the team creator
        TeamMembership.objects.create(team=team, player=creator, member_status=True)

        # Update member count after creation
        team.member_count = 1
        team.save()

    def perform_update(self, serializer):
        # Update member count when a member is added
        serializer.save()
        team = serializer.instance
        team.member_count = team.memberships.count()
        team.save()

    def get_queryset(self):
        return Team.objects.filter(memberships__player=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        if serializer.instance.member_count >= 5:
            serializer.instance.created = True
            serializer.instance.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# დასატესტია!!!!
# Invitations
class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # This allows users to see invitations they've sent and received
        return Invitation.objects.filter(Q(sender__creator=user) | Q(receiver=user))

    def create(self, request, *args, **kwargs):
        # Custom logic for creating an invitation, including validation
        # and sending a notification to the receiver.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Assuming `sender` is a team ID passed in the request
        team_id = serializer.validated_data['sender'].id
        team = get_object_or_404(Team, id=team_id)

        if team.memberships.count() >= 7:
            return Response({"error": "Team cannot have more than 7 members"}, status=status.HTTP_400_BAD_REQUEST)

        receiver = serializer.validated_data['receiver']
        if TeamMembership.objects.filter(team=team, player=receiver, member_status=True).exists():
            return Response({"error": "User already has an active membership in the team"}, status=status.HTTP_400_BAD_REQUEST)

        Notification.objects.create(user=receiver, message="You have received an invitation to join a team")
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # This method is called by the create method.
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        # Restrict updates to the status field for PATCH requests.
        if 'status' in request.data and len(request.data) == 1:
            invitation = self.get_object()

            if invitation.receiver != request.user:
                return Response({"error": "You do not have permission to update this invitation."}, status=status.HTTP_403_FORBIDDEN)

            new_status = request.data['status']
            if new_status not in ['Accepted', 'Declined']:
                return Response({"error": "Invalid status. Only 'Accepted' or 'Declined' are allowed."}, status=status.HTTP_400_BAD_REQUEST)

            if invitation.status == 'Pending':
                response = super().partial_update(request, *args, **kwargs)
                if response.status_code == status.HTTP_200_OK:
                    # Notifications for both the receiver and the sender
                    Notification.objects.create(user=request.user, message=f"You have {new_status.lower()} the invitation to join {invitation.sender.name}.")
                    Notification.objects.create(user=invitation.sender.creator, message=f"{request.user.username} has {new_status.lower()} the invitation to join {invitation.sender.name}.")
                return response
        else:
            return Response({"error": "You can only update the status."}, status=status.HTTP_400_BAD_REQUEST)
