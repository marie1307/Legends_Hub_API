from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserRegistrationSerializer, LoginSerializer, CustomUserSerializer, TeamSerializer, TeamMembershipSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from . models import CustomUser, Team, TeamMembership
from .permissions import PersinalPagePermission
from rest_framework.exceptions import MethodNotAllowed


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
        if 'password' not in request.data:
            return Response({'error': 'Password field is required'}, status=status.HTTP_400_BAD_REQUEST)
        password = request.data['password']
        user.set_password(password)
        user.save()
        return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
    
    # Updates in_game_name only
    def update(self, request, *args, **kwargs):
        user = self.request.user
        if 'in_game_name' not in request.data:
            return Response({'error': 'In-game name field is required'}, status=status.HTTP_400_BAD_REQUEST)
        in_game_name = request.data['in_game_name']
        user.in_game_name = in_game_name
        user.save()
        return Response({'message': 'In-game name updated successfully'}, status=status.HTTP_200_OK)
         

class TeamMembershipViewSet(viewsets.ModelViewSet):
    queryset = TeamMembership.objects.all()
    serializer_class = TeamMembershipSerializer
    authentication_classes = [TokenAuthentication]

    # # Get information only owner
    # def get_queryset(self):
    #     user = self.request.user
    #     return CustomUser.objects.filter(username=user)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def perform_create(self, serializer):
        team = serializer.save(creator=self.request.user)
        # Automatically assign captain status to the team creator
        TeamMembership.objects.create(team=team, player=self.request.user, role='Captain')
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
        if 8 < serializer.instance.member_count >= 5:
            serializer.instance.created = True
            serializer.instance.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
