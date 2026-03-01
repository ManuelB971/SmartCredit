"""
Models for the simulation app.
Core data models: Utilisateur, Simulation, ProfilFinancier, ProjetCredit, OffreBancaire...
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

# ========================
# UTILISATEURS (Users app)
# ========================
class Utilisateur(AbstractUser):
    """Extended User model for Smart Crédit."""

    SITUATION_CHOICES = (
        ('CELIBATAIRE', 'Célibataire'),
        ('MARIE', 'Marié'),
        ('PACSE', 'Pacsé'),
        ('CONCUBINAGE', 'En concubinage'),
    )

    phone = models.CharField(max_length=20, blank=True)
    situation_familiale = models.CharField(
        max_length=20,
        choices=SITUATION_CHOICES,
        blank=True
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'utilisateurs'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"


# ========================
# SIMULATIONS
# ========================
class Simulation(models.Model):
    """Main simulation instance."""

    TYPE_CREDIT_CHOICES = (
        ('ETUDIANT', 'Crédit Étudiant'),
        ('IMMOBILIER', 'Crédit Immobilier'),
    )

    STATUT_CHOICES = (
        ('CREEE', 'Créée'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('ERREUR', 'Erreur'),
    )

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='simulations',
        null=True,
        blank=True
    )
    type_credit = models.CharField(max_length=20, choices=TYPE_CREDIT_CHOICES)
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='CREEE'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'simulations'
        verbose_name = 'Simulation'
        verbose_name_plural = 'Simulations'
        ordering = ['-date_creation']

    def __str__(self):
        return f"Simulation {self.id} - {self.type_credit}"


# ========================
# PROFIL FINANCIER
# ========================
class ProfilFinancier(models.Model):
    """User financial profile for the simulation."""

    TYPE_CONTRAT_CHOICES = (
        ('CDI', 'CDI'),
        ('CDD', 'CDD'),
        ('STAGE', 'Stage'),
        ('ALTERNANCE', 'Alternance'),
        ('TRAVAILLEUR_INDEPENDANT', 'Travailleur indépendant'),
        ('ASSIMILE_SALARIE', 'Assimilé salarié'),
        ('SANS_EMPLOI', 'Sans emploi'),
        ('RETRAITE', 'Retraité'),
        ('ETUDIANT', 'Étudiant'),
    )

    simulation = models.OneToOneField(
        Simulation,
        on_delete=models.CASCADE,
        related_name='profil_financier'
    )

    # Informations personnelles
    age = models.IntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(100)]
    )
    situation_familiale = models.CharField(
        max_length=20,
        choices=Utilisateur._meta.get_field('situation_familiale').choices
    )
    ville = models.CharField(max_length=100)

    # Revenus
    revenus_mensuels = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Charges
    charges_logement = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Loyer ou mensualité crédit immobilier"
    )
    charges_credits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total des mensualités des crédits en cours"
    )
    charges_autres = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text="Autres charges (voiture, assurance, etc.)"
    )

    # Emploi
    type_contrat = models.CharField(max_length=50, choices=TYPE_CONTRAT_CHOICES)
    anciennete_emploi_mois = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="En mois"
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'profils_financiers'
        verbose_name = 'Profil Financier'
        verbose_name_plural = 'Profils Financiers'

    def __str__(self):
        return f"Profil Sim#{self.simulation.id}"

    @property
    def charges_totales(self):
        """Total de toutes les charges mensuelles."""
        return self.charges_logement + self.charges_credits + self.charges_autres

    @property
    def taux_endettement_actuel(self):
        """Current debt ratio (%)."""
        if self.revenus_mensuels == 0:
            return 0
        return (self.charges_totales / self.revenus_mensuels) * 100


# ========================
# PROJET DE CRÉDIT
# ========================
class ProjetCredit(models.Model):
    """Credit project details."""

    simulation = models.OneToOneField(
        Simulation,
        on_delete=models.CASCADE,
        related_name='projet_credit'
    )

    montant_souhaite = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(100)]
    )
    duree_mois = models.IntegerField(validators=[MinValueValidator(1)])
    apport_personnel = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projets_credit'
        verbose_name = 'Projet de Crédit'
        verbose_name_plural = 'Projets de Crédit'

    def __str__(self):
        return f"Projet Sim#{self.simulation.id} - {self.montant_souhaite}€"


# ========================
# OFFRES BANCAIRES
# ========================
class OffreBancaire(models.Model):
    """Bank offers database."""

    TYPE_CREDIT_CHOICES = Simulation._meta.get_field('type_credit').choices

    banque = models.CharField(max_length=100)
    type_credit = models.CharField(max_length=20, choices=TYPE_CREDIT_CHOICES)
    taux_interet = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="En pourcentage"
    )

    # Pour crédit immobilier
    duree_min_mois = models.IntegerField(null=True, blank=True)
    duree_max_mois = models.IntegerField(null=True, blank=True)

    # Pour crédit étudiant
    montant_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'offres_bancaires'
        verbose_name = 'Offre Bancaire'
        verbose_name_plural = 'Offres Bancaires'
        unique_together = ('banque', 'type_credit', 'duree_min_mois')

    def __str__(self):
        return f"{self.banque} - {self.type_credit} ({self.taux_interet}%)"


# ========================
# RÉSULTATS DE SIMULATION
# ========================
class ResultatSimulation(models.Model):
    """Simulation results - one per scenario."""

    SCENARIO_CHOICES = (
        ('PRUDENT', 'Prudent'),
        ('EQUILIBRE', 'Équilibré'),
        ('CONFORTABLE', 'Confortable'),
    )

    simulation = models.ForeignKey(
        Simulation,
        on_delete=models.CASCADE,
        related_name='resultats'
    )
    offre_bancaire = models.ForeignKey(
        OffreBancaire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    scenario = models.CharField(max_length=20, choices=SCENARIO_CHOICES)
    taux_utilise = models.DecimalField(max_digits=5, decimal_places=3)

    # Résultats financiers
    mensualite = models.DecimalField(max_digits=10, decimal_places=2)
    cout_total = models.DecimalField(max_digits=12, decimal_places=2)

    # Indicateurs
    taux_endettement_nouveau = models.DecimalField(max_digits=5, decimal_places=2)
    reste_a_vivre = models.DecimalField(max_digits=10, decimal_places=2)
    score_faisabilite = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resultats_simulations'
        verbose_name = 'Résultat de Simulation'
        verbose_name_plural = 'Résultats de Simulations'

    def __str__(self):
        return f"Sim#{self.simulation.id} - {self.scenario}: {self.mensualite}€/mois"


# ========================
# EXPLICATIONS IA
# ========================
class ExplicationIA(models.Model):
    """AI-generated explanations."""

    simulation = models.OneToOneField(
        Simulation,
        on_delete=models.CASCADE,
        related_name='explication_ia'
    )

    texte = models.TextField()
    recommandations = models.TextField(blank=True)
    avertissements = models.TextField(blank=True, null=True)

    date_generation = models.DateTimeField(auto_now_add=True)
    temps_generation_ms = models.IntegerField(default=0)

    class Meta:
        db_table = 'explications_ia'
        verbose_name = 'Explication IA'
        verbose_name_plural = 'Explications IA'

    def __str__(self):
        return f"Explication Sim#{self.simulation.id}"
