"""
Serializers for users app.
"""

from rest_framework import serializers
from simulation.models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    """Serializer for Utilisateur model."""

    class Meta:
        model = Utilisateur
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'situation_familiale', 'date_creation']
        read_only_fields = ['id', 'date_creation']
