"""
Admin configuration for simulation app.
"""

from django.contrib import admin
from .models import (
    Utilisateur, Simulation, ProfilFinancier, ProjetCredit,
    OffreBancaire, ResultatSimulation, ExplicationIA
)


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'situation_familiale', 'date_creation')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('situation_familiale', 'date_creation')


@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_credit', 'statut', 'utilisateur', 'date_creation')
    search_fields = ('id', 'utilisateur__email')
    list_filter = ('type_credit', 'statut', 'date_creation')


@admin.register(ProfilFinancier)
class ProfilFinancierAdmin(admin.ModelAdmin):
    list_display = ('simulation', 'age', 'situation_familiale', 'revenus_mensuels', 'taux_endettement_actuel')
    search_fields = ('simulation__id',)
    list_filter = ('situation_familiale', 'type_contrat')


@admin.register(ProjetCredit)
class ProjetCreditAdmin(admin.ModelAdmin):
    list_display = ('simulation', 'montant_souhaite', 'duree_mois', 'apport_personnel')
    search_fields = ('simulation__id',)


@admin.register(OffreBancaire)
class OffreBancaireAdmin(admin.ModelAdmin):
    list_display = ('banque', 'type_credit', 'taux_interet', 'actif', 'date_mise_a_jour')
    search_fields = ('banque',)
    list_filter = ('type_credit', 'actif', 'date_mise_a_jour')


@admin.register(ResultatSimulation)
class ResultatSimulationAdmin(admin.ModelAdmin):
    list_display = ('simulation', 'scenario', 'mensualite', 'score_faisabilite', 'taux_endettement_nouveau')
    search_fields = ('simulation__id',)
    list_filter = ('scenario', 'date_creation')


@admin.register(ExplicationIA)
class ExplicationIAAdmin(admin.ModelAdmin):
    list_display = ('simulation', 'temps_generation_ms', 'date_generation')
    search_fields = ('simulation__id',)
