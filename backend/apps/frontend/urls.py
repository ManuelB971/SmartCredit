from django.urls import path

from . import views

app_name = "frontend"

urlpatterns = [
    path("", views.LandingView.as_view(), name="landing"),
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    path("inscription/", views.InscriptionView.as_view(), name="inscription"),
    path("simulation/etape-1/", views.SimulationEtape1View.as_view(), name="etape1"),
    path("simulation/etape-2/", views.SimulationEtape2View.as_view(), name="etape2"),
    path("simulation/etape-3/", views.SimulationEtape3View.as_view(), name="etape3"),
    path("simulation/analyse/<int:simulation_id>/", views.AnalyseView.as_view(), name="analyse"),
    path("simulation/resultats/<int:simulation_id>/", views.TableauBordView.as_view(), name="resultats"),
    path("deconnexion/", views.DeconnexionView.as_view(), name="deconnexion"),
    path("mon-compte/", views.MonCompteView.as_view(), name="mon_compte"),
]
