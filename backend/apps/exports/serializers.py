from rest_framework import serializers

from .models import ExportPdfEmail


class ExportEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ExportPdfEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportPdfEmail
        fields = ["id", "simulation_id", "email_destinataire", "etat", "date_demande", "date_envoi", "erreur"]

