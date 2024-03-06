from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserRegistrationSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from . models import CustomUser
from django.db.models import Q



# Registration
class RegistrationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        x = CustomUser.objects.filter(Q(username=request.data["username"])&Q(in_game_name=request.data["in_game_name"]))
        print(x)
                                       
        if serializer.is_valid() and len(x)==0:
            user = serializer.save()

            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'user': serializer.data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response({"status":"User already exists"}, status=status.HTTP_400_BAD_REQUEST)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
