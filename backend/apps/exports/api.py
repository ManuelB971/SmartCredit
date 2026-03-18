from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.credit.models import Simulation
from .models import ExportPdfEmail
from .serializers import ExportEmailRequestSerializer, ExportPdfEmailSerializer


@extend_schema(
    tags=["Exports"],
    summary="Demander l'envoi email du PDF récapitulatif (traçabilité MVP)",
    description=(
        "Crée une entrée de traçabilité pour l'UC4 (email + PDF). Pour le MVP1, cette API **enregistre la demande**.\n\n"
        "Implémentation future:\n"
        "- génération PDF\n"
        "- envoi email asynchrone (Celery/queue)\n"
        "- passage de `etat` à `ENVOYE` ou `ECHEC`"
    ),
    request=ExportEmailRequestSerializer,
    responses={
        201: ExportPdfEmailSerializer,
        400: OpenApiResponse(description="Email requis / invalide"),
        404: OpenApiResponse(description="Simulation introuvable"),
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

    export = ExportPdfEmail.objects.create(simulation=sim, email_destinataire=serializer.validated_data["email"])
    return Response(ExportPdfEmailSerializer(export).data, status=status.HTTP_201_CREATED)

