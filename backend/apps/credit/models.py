from django.db import models
from django.db.models import Q


class TypeCredit(models.TextChoices):
    ETUDIANT = "ETUDIANT"
    IMMOBILIER = "IMMOBILIER"


class StatutSimulation(models.TextChoices):
    EN_COURS = "EN_COURS"
    TERMINEE = "TERMINEE"


class ScenarioResultat(models.TextChoices):
    PRUDENT = "PRUDENT"
    EQUILIBRE = "EQUILIBRE"
    CONFORT = "CONFORT"


class NiveauLangage(models.TextChoices):
    ETUDIANT = "ETUDIANT"
    STANDARD = "STANDARD"
    PROFESSIONNEL = "PROFESSIONNEL"


class Simulation(models.Model):
    type_credit = models.CharField(max_length=20, choices=TypeCredit.choices)
    date_simulation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=StatutSimulation.choices, default=StatutSimulation.EN_COURS)
    utilisateur = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="simulations"
    )
    source = models.CharField(max_length=30, default="web")
    ip_hash = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["utilisateur"]),
            models.Index(fields=["date_simulation"]),
            models.Index(fields=["type_credit"]),
        ]


class ProfilFinancier(models.Model):
    age = models.PositiveIntegerField()
    situation_familiale = models.CharField(max_length=20)
    nombre_enfants = models.PositiveIntegerField(default=0)
    ville = models.CharField(max_length=100, null=True, blank=True)
    revenus_mensuels = models.DecimalField(max_digits=10, decimal_places=2)
    autres_revenus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charges_logement = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charges_credits = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    autres_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    type_contrat = models.CharField(max_length=20, null=True, blank=True)
    anciennete_emploi_mois = models.PositiveIntegerField(null=True, blank=True)
    simulation = models.OneToOneField(Simulation, on_delete=models.CASCADE, related_name="profil_financier")

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(age__gte=18) & Q(age__lte=100), name="profil_age_ck"),
            models.CheckConstraint(check=Q(revenus_mensuels__gte=0), name="profil_revenus_ck"),
            models.CheckConstraint(check=Q(autres_revenus__gte=0), name="profil_autres_revenus_ck"),
            models.CheckConstraint(check=Q(charges_logement__gte=0), name="profil_charges_logement_ck"),
            models.CheckConstraint(check=Q(charges_credits__gte=0), name="profil_charges_credits_ck"),
            models.CheckConstraint(check=Q(autres_charges__gte=0), name="profil_autres_charges_ck"),
        ]


class ProjetCredit(models.Model):
    type_credit = models.CharField(max_length=20, choices=TypeCredit.choices)
    montant_souhaite = models.DecimalField(max_digits=12, decimal_places=2)
    duree_mois = models.PositiveIntegerField()
    apport_personnel = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    simulation = models.OneToOneField(Simulation, on_delete=models.CASCADE, related_name="projet_credit")

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(montant_souhaite__gt=0), name="projet_montant_ck"),
            models.CheckConstraint(check=Q(duree_mois__gt=0), name="projet_duree_ck"),
            models.CheckConstraint(check=Q(apport_personnel__gte=0), name="projet_apport_ck"),
        ]


class Banque(models.Model):
    nom = models.CharField(max_length=150, unique=True)
    site_url = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.nom


class OffreBancaire(models.Model):
    banque = models.ForeignKey(Banque, on_delete=models.RESTRICT, related_name="offres")
    type_credit = models.CharField(max_length=20, choices=TypeCredit.choices)
    duree_min_mois = models.PositiveIntegerField()
    duree_max_mois = models.PositiveIntegerField()
    taux_annuel = models.DecimalField(max_digits=5, decimal_places=3)
    conditions_particulieres = models.TextField(null=True, blank=True)
    date_mise_a_jour = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(duree_min_mois__gt=0), name="offre_duree_min_ck"),
            models.CheckConstraint(check=Q(duree_max_mois__gte=models.F("duree_min_mois")), name="offre_duree_range_ck"),
            models.CheckConstraint(check=Q(taux_annuel__gte=0), name="offre_taux_ck"),
        ]
        indexes = [
            models.Index(fields=["type_credit"]),
            models.Index(fields=["banque", "type_credit"]),
            models.Index(fields=["date_mise_a_jour"]),
        ]


class ResultatSimulation(models.Model):
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name="resultats")
    offre_bancaire = models.ForeignKey(OffreBancaire, null=True, blank=True, on_delete=models.SET_NULL)

    mensualite = models.DecimalField(max_digits=10, decimal_places=2)
    taux_utilise = models.DecimalField(max_digits=5, decimal_places=3)
    cout_total = models.DecimalField(max_digits=12, decimal_places=2)
    taux_endettement = models.DecimalField(max_digits=5, decimal_places=2)
    reste_a_vivre = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    score_faisabilite = models.PositiveSmallIntegerField(null=True, blank=True)
    scenario = models.CharField(max_length=20, choices=ScenarioResultat.choices, null=True, blank=True)
    date_calcul = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(score_faisabilite__isnull=True) | (Q(score_faisabilite__gte=0) & Q(score_faisabilite__lte=100)), name="resultat_score_ck"),
            models.CheckConstraint(check=Q(mensualite__gte=0), name="resultat_mensualite_ck"),
            models.CheckConstraint(check=Q(cout_total__gte=0), name="resultat_cout_ck"),
            models.CheckConstraint(check=Q(taux_endettement__gte=0), name="resultat_endettement_ck"),
            models.CheckConstraint(check=Q(reste_a_vivre__isnull=True) | Q(reste_a_vivre__gte=0), name="resultat_reste_ck"),
        ]
        indexes = [
            models.Index(fields=["simulation"]),
            models.Index(fields=["offre_bancaire"]),
        ]


class ExplicationIA(models.Model):
    simulation = models.OneToOneField(Simulation, on_delete=models.CASCADE, related_name="explication_ia")
    texte_explication = models.TextField()
    recommandations = models.TextField(null=True, blank=True)
    avertissements = models.TextField(null=True, blank=True)
    resume_executif = models.TextField(blank=True, default="")
    donnees_enrichies = models.JSONField(default=dict, blank=True)  # points_forts_dossier, risques_identifies, prochaines_etapes
    niveau_langage = models.CharField(max_length=20, choices=NiveauLangage.choices, default=NiveauLangage.STANDARD)
    date_generation = models.DateTimeField(auto_now_add=True)

