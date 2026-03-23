from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import login, logout

from .serializers import RegisterSerializer, LoginSerializer, MeSerializer
from apps.credit.models import Simulation


@csrf_exempt
@extend_schema(
    tags=["Auth"],
    summary="Créer un compte",
    request=RegisterSerializer,
    responses={201: RegisterSerializer, 409: OpenApiResponse(description="Email déjà utilisé")},
    examples=[
        OpenApiExample(
            "Exemple inscription",
            value={"email": "lea@example.com", "password": "motdepassefort", "nom": "Dupont", "prenom": "Léa"},
            request_only=True,
        ),
        OpenApiExample(
            "Inscription + sauvegarde simulation",
            value={"email": "lea@example.com", "password": "motdepassefort", "nom": "Dupont", "prenom": "Léa", "simulation_id": 42},
            request_only=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].lower()
    if serializer.Meta.model.objects.filter(email=email).exists():
        return Response({"error": "Email déjà utilisé"}, status=409)
    simulation_id = serializer.validated_data.pop("simulation_id", None)
    user = serializer.save(email=email)
    if simulation_id:
        Simulation.objects.filter(id=simulation_id, utilisateur__isnull=True).update(utilisateur=user)
    login(request, user)
    return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="Se connecter (session)",
    description=(
        "Ouvre une session Django.\n\n"
        "Notes:\n"
        "- Les requêtes suivantes peuvent utiliser le cookie de session.\n"
        "- Pour tester dans Swagger UI: exécuter d'abord `login`, puis appeler des endpoints protégés (ex: `/api/auth/me/`)."
    ),
    request=LoginSerializer,
    responses={200: OpenApiResponse(description="OK"), 401: OpenApiResponse(description="Identifiants invalides")},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    login(request, user)
    return Response({"ok": True})


@extend_schema(
    tags=["Auth"],
    summary="Se déconnecter (session)",
    description="Ferme la session courante (cookie).",
    responses={200: OpenApiResponse(description="OK")},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({"ok": True})


@extend_schema(
    tags=["Auth"],
    summary="Profil courant",
    description="Retourne l'utilisateur courant (authentification requise).",
    responses={200: MeSerializer, 204: OpenApiResponse(description="Compte supprimé")},
)
@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == "DELETE":
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(MeSerializer(request.user).data)

