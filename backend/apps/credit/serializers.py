from rest_framework import serializers

from .models import (
    Simulation,
    ProfilFinancier,
    ProjetCredit,
    ResultatSimulation,
    ExplicationIA,
    OffreBancaire,
    Banque,
)


class ProfilFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilFinancier
        exclude = ["id", "simulation"]


class ProjetCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjetCredit
        exclude = ["id", "simulation"]


class SimulationCreateSerializer(serializers.Serializer):
    type_credit = serializers.ChoiceField(choices=Simulation._meta.get_field("type_credit").choices)
    profil_financier = ProfilFinancierSerializer()
    projet_credit = ProjetCreditSerializer()

    def create(self, validated_data):
        profil = validated_data.pop("profil_financier")
        projet = validated_data.pop("projet_credit")
        request = self.context["request"]
        sim = Simulation.objects.create(
            type_credit=validated_data["type_credit"],
            utilisateur=request.user if request.user.is_authenticated else None,
        )
        ProfilFinancier.objects.create(simulation=sim, **profil)
        ProjetCredit.objects.create(simulation=sim, **projet)
        return sim


class BanqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banque
        fields = ["id", "nom", "site_url"]


class OffreBancaireSerializer(serializers.ModelSerializer):
    banque = BanqueSerializer()

    class Meta:
        model = OffreBancaire
        fields = [
            "id",
            "banque",
            "type_credit",
            "duree_min_mois",
            "duree_max_mois",
            "taux_annuel",
            "conditions_particulieres",
            "date_mise_a_jour",
        ]


class ResultatSimulationSerializer(serializers.ModelSerializer):
    offre_bancaire = OffreBancaireSerializer(allow_null=True)
    montant_total_rembourse = serializers.SerializerMethodField()

    class Meta:
        model = ResultatSimulation
        fields = [
            "id",
            "scenario",
            "mensualite",
            "taux_utilise",
            "cout_total",
            "montant_total_rembourse",
            "taux_endettement",
            "reste_a_vivre",
            "score_faisabilite",
            "date_calcul",
            "offre_bancaire",
        ]

    def get_montant_total_rembourse(self, obj):
        capital = obj.simulation.projet_credit.montant_souhaite - obj.simulation.projet_credit.apport_personnel
        return float(capital + obj.cout_total)


class ExplicationIASerializer(serializers.ModelSerializer):
    class Meta:
        model = ExplicationIA
        fields = [
            "texte_explication",
            "recommandations",
            "avertissements",
            "resume_executif",
            "donnees_enrichies",
            "niveau_langage",
            "date_generation",
        ]


class SimulationDetailSerializer(serializers.ModelSerializer):
    profil_financier = ProfilFinancierSerializer()
    projet_credit = ProjetCreditSerializer()
    resultats = ResultatSimulationSerializer(many=True)
    explication_ia = ExplicationIASerializer(allow_null=True)

    class Meta:
        model = Simulation
        fields = [
            "id",
            "type_credit",
            "date_simulation",
            "statut",
            "utilisateur_id",
            "profil_financier",
            "projet_credit",
            "resultats",
            "explication_ia",
        ]

