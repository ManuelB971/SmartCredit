from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView


BANK_NAMES = [
    "BNP Paribas", "Crédit Agricole", "Société Générale", "Boursorama Banque",
    "Banque Populaire", "Crédit Mutuel", "Caisse d'Épargne", "Pretto", "Bpifrance",
]


class LandingView(TemplateView):
    template_name = "landing_page.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bank_list"] = BANK_NAMES
        return ctx


class ConnexionView(TemplateView):
    template_name = "auth/connexion.html"


class InscriptionView(TemplateView):
    template_name = "auth/inscription.html"


class SimulationEtape1View(TemplateView):
    template_name = "simulation/etape1_profil.html"


class SimulationEtape2View(TemplateView):
    template_name = "simulation/etape2_revenus.html"


class SimulationEtape3View(TemplateView):
    template_name = "simulation/etape3_projet.html"


class AnalyseView(TemplateView):
    template_name = "simulation/analyse_ia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["simulation_id"] = self.kwargs.get("simulation_id")
        return context


class TableauBordView(TemplateView):
    template_name = "simulation/tableau_bord.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["simulation_id"] = self.kwargs.get("simulation_id")
        return context


class DeconnexionView(View):
    def post(self, request):
        logout(request)
        return redirect("/")


class MonCompteView(TemplateView):
    template_name = "account/mon_compte.html"
