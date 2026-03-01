"""
REST Framework serializers for the simulation app.
"""

from rest_framework import serializers
from .models import (
    Utilisateur, Simulation, ProfilFinancier, ProjetCredit,
    OffreBancaire, ResultatSimulation, ExplicationIA
)


class UtilisateurSerializer(serializers.ModelSerializer):
    """Serializer for Utilisateur model."""

    class Meta:
        model = Utilisateur
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'situation_familiale', 'date_creation']
        read_only_fields = ['id', 'date_creation']


class ProfilFinancierSerializer(serializers.ModelSerializer):
    """Serializer for ProfilFinancier model."""

    charges_totales = serializers.SerializerMethodField()
    taux_endettement_actuel = serializers.SerializerMethodField()

    class Meta:
        model = ProfilFinancier
        fields = [
            'id', 'age', 'situation_familiale', 'ville',
            'revenus_mensuels', 'charges_logement', 'charges_credits', 'charges_autres',
            'charges_totales', 'taux_endettement_actuel',
            'type_contrat', 'anciennete_emploi_mois'
        ]
        read_only_fields = ['id', 'charges_totales', 'taux_endettement_actuel']

    def get_charges_totales(self, obj):
        return obj.charges_totales

    def get_taux_endettement_actuel(self, obj):
        return obj.taux_endettement_actuel


class ProjetCreditSerializer(serializers.ModelSerializer):
    """Serializer for ProjetCredit model."""

    class Meta:
        model = ProjetCredit
        fields = ['id', 'montant_souhaite', 'duree_mois', 'apport_personnel']
        read_only_fields = ['id']


class OffreBancaireSerializer(serializers.ModelSerializer):
    """Serializer for OffreBancaire model."""

    class Meta:
        model = OffreBancaire
        fields = [
            'id', 'banque', 'type_credit', 'taux_interet',
            'duree_min_mois', 'duree_max_mois', 'montant_max',
            'description', 'actif'
        ]
        read_only_fields = ['id']


class ResultatSimulationSerializer(serializers.ModelSerializer):
    """Serializer for ResultatSimulation model."""

    offre_bancaire = OffreBancaireSerializer(read_only=True)

    class Meta:
        model = ResultatSimulation
        fields = [
            'id', 'scenario', 'taux_utilise', 'mensualite', 'cout_total',
            'taux_endettement_nouveau', 'reste_a_vivre', 'score_faisabilite',
            'offre_bancaire'
        ]
        read_only_fields = ['id']


class ExplicationIASerializer(serializers.ModelSerializer):
    """Serializer for ExplicationIA model."""

    class Meta:
        model = ExplicationIA
        fields = ['id', 'texte', 'recommandations', 'avertissements', 'temps_generation_ms']
        read_only_fields = ['id', 'temps_generation_ms']


class SimulationDetailSerializer(serializers.ModelSerializer):
    """Detailed Simulation serializer with all related data."""

    profil_financier = ProfilFinancierSerializer(read_only=True)
    projet_credit = ProjetCreditSerializer(read_only=True)
    resultats = ResultatSimulationSerializer(many=True, read_only=True)
    explication_ia = ExplicationIASerializer(read_only=True)

    class Meta:
        model = Simulation
        fields = [
            'id', 'type_credit', 'statut',
            'profil_financier', 'projet_credit',
            'resultats', 'explication_ia',
            'date_creation', 'date_modification'
        ]
        read_only_fields = ['id', 'statut', 'date_creation', 'date_modification']


class SimulationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating simulations with nested data."""

    profil_financier = ProfilFinancierSerializer(required=True)
    projet_credit = ProjetCreditSerializer(required=True)

    class Meta:
        model = Simulation
        fields = ['type_credit', 'profil_financier', 'projet_credit']

    def create(self, validated_data):
        profil_data = validated_data.pop('profil_financier')
        projet_data = validated_data.pop('projet_credit')

        simulation = Simulation.objects.create(**validated_data)
        ProfilFinancier.objects.create(simulation=simulation, **profil_data)
        ProjetCredit.objects.create(simulation=simulation, **projet_data)

        return simulation
