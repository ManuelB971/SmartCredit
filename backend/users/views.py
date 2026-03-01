"""
Views for users app (authentication).
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

from simulation.models import Utilisateur
from .serializers import UtilisateurSerializer


class UserViewSet(viewsets.ViewSet):
    """
    User management API endpoints.
    """

    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register new user.
        POST /api/users/register/
        """
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Utilisateur.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = Utilisateur.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'user': UtilisateurSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Login user and return token.
        POST /api/users/login/
        """
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = Utilisateur.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'user': UtilisateurSerializer(user).data,
            'token': token.key
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile."""
        return Response(UtilisateurSerializer(request.user).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def simulations(self, request):
        """Get current user's simulation history."""
        from simulation.models import Simulation
        from simulation.serializers import SimulationDetailSerializer

        simulations = Simulation.objects.filter(utilisateur=request.user)
        serializer = SimulationDetailSerializer(simulations, many=True)
        return Response(serializer.data)
