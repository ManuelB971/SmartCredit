from django.views.generic import TemplateView


class LandingView(TemplateView):
    template_name = "landing_page.html"


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


class HistoriqueView(TemplateView):
    template_name = "simulation/historique.html"
