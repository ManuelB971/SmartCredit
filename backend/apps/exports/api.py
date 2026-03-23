from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.credit.models import Simulation
from .models import ExportPdfEmail
from .pdf_service import send_simulation_pdf_email, is_email_configured
from .serializers import ExportEmailRequestSerializer, ExportPdfEmailSerializer


@extend_schema(
    tags=["Exports"],
    summary="Demander l'envoi email du PDF récapitulatif",
    description=(
        "Génère le rapport PDF de la simulation et l'envoie par email au destinataire. "
        "Nécessite la configuration email dans .env (EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)."
    ),
    request=ExportEmailRequestSerializer,
    responses={
        201: ExportPdfEmailSerializer,
        400: OpenApiResponse(description="Email requis / invalide"),
        404: OpenApiResponse(description="Simulation introuvable"),
        503: OpenApiResponse(description="Configuration email manquante"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def export_email(request, simulation_id: int):
    serializer = ExportEmailRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        sim = Simulation.objects.get(id=simulation_id)
    except Simulation.DoesNotExist:
        return Response({"error": "Simulation introuvable"}, status=404)

    if not is_email_configured():
        return Response(
            {"error": "L'envoi d'email n'est pas configuré. Vérifiez EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD dans .env"},
            status=503,
        )

    export = ExportPdfEmail.objects.create(simulation=sim, email_destinataire=serializer.validated_data["email"])
    success = send_simulation_pdf_email(export)
    return Response(
        ExportPdfEmailSerializer(export).data,
        status=status.HTTP_201_CREATED,
    )

