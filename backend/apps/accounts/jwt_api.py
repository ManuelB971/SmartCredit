from django.contrib.auth import login
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


@extend_schema(
    tags=["Auth"],
    summary="Obtenir un token JWT (access + refresh)",
    request=TokenObtainPairSerializer,
    responses={200: OpenApiResponse(description="Tokens JWT")},
    examples=[
        OpenApiExample(
            "Exemple",
            value={"email": "manuel@gmail.com", "password": "motdepassefort"},
            request_only=True,
        )
    ],
)
class SmartCreditTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login(request, serializer.user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    summary="Rafraîchir un token JWT (access)",
    request=TokenRefreshSerializer,
    responses={200: OpenApiResponse(description="Nouveau token access")},
)
class SmartCreditTokenRefreshView(TokenRefreshView):
    pass

