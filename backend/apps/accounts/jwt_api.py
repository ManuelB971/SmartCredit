from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
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
    pass


@extend_schema(
    tags=["Auth"],
    summary="Rafraîchir un token JWT (access)",
    request=TokenRefreshSerializer,
    responses={200: OpenApiResponse(description="Nouveau token access")},
)
class SmartCreditTokenRefreshView(TokenRefreshView):
    pass

