"""
Views and ViewSets for the simulation app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import Simulation, OffreBancaire, ProfilFinancier, ProjetCredit, ResultatSimulation, ExplicationIA
from .serializers import (
    SimulationDetailSerializer, SimulationCreateSerializer, OffreBancaireSerializer
)
from .services.calculs import CalculService, ScoringService
from .services.ia_service import IAService


class SimulationViewSet(viewsets.ModelViewSet):
    """
    Simulation API endpoint.

    Actions:
    - POST /simulations/ - Create new simulation
    - GET /simulations/{id}/ - Get simulation details
    - POST /simulations/{id}/calcul/ - Run calculation and IA
    - GET /simulations/{id}/pdf/ - Generate PDF report
    - POST /simulations/{id}/email/ - Send results by email
    """

    permission_classes = [AllowAny]
    serializer_class = SimulationDetailSerializer

    def get_queryset(self):
        """Filter simulations by current user if authenticated."""
        if self.request.user.is_authenticated:
            return Simulation.objects.filter(utilisateur=self.request.user)
        return Simulation.objects.none()

    def create(self, request, *args, **kwargs):
        """Create new simulation with initial data."""
        serializer = SimulationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        simulation = serializer.instance
        return Response(
            SimulationDetailSerializer(simulation).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def calcul(self, request, pk=None):
        """
        Run calculation and generate IA explanation.

        POST /api/simulation/{id}/calcul/
        """
        simulation = self.get_object()

        try:
            # Get related objects
            profil = simulation.profil_financier
            projet = simulation.projet_credit

            # Find best offers
            offres = OffreBancaire.objects.filter(
                type_credit=simulation.type_credit,
                actif=True
            ).order_by('taux_interet')

            # Remove old results
            simulation.resultats.all().delete()

            # Create results for 3 scenarios
            scenarios = [
                ('PRUDENT', offres.first() if offres.exists() else None),
                ('EQUILIBRE', offres[1] if len(offres) > 1 else offres.first()),
                ('CONFORTABLE', offres.last() if offres.exists() else None),
            ]

            resultats_list = []

            for scenario, offre in scenarios:
                if not offre:
                    continue

                # Calculate metrics
                capital = float(projet.montant_souhaite) - float(projet.apport_personnel)
                mensualite = CalculService.calculer_mensualite(
                    capital,
                    float(offre.taux_interet),
                    projet.duree_mois
                )
                cout_total = CalculService.calculer_cout_total(
                    mensualite,
                    projet.duree_mois,
                    capital
                )

                charges_avec_credit = profil.charges_totales + mensualite
                taux_endettement = CalculService.calculer_taux_endettement(
                    charges_avec_credit,
                    profil.revenus_mensuels
                )
                reste_a_vivre = CalculService.calculer_reste_a_vivre(
                    profil.revenus_mensuels,
                    profil.charges_totales,
                    mensualite
                )

                # Calculate score
                score = ScoringService.calculer_score(
                    {
                        'type_contrat': profil.type_contrat,
                        'anciennete_emploi_mois': profil.anciennete_emploi_mois,
                        'age': profil.age
                    },
                    {
                        'taux_endettement_nouveau': taux_endettement,
                        'reste_a_vivre': reste_a_vivre,
                        'apport_ratio': float(projet.apport_personnel) / float(projet.montant_souhaite) if projet.montant_souhaite > 0 else 0
                    }
                )

                # Create result
                resultat = ResultatSimulation.objects.create(
                    simulation=simulation,
                    offre_bancaire=offre,
                    scenario=scenario,
                    taux_utilise=offre.taux_interet,
                    mensualite=mensualite,
                    cout_total=cout_total,
                    taux_endettement_nouveau=taux_endettement,
                    reste_a_vivre=reste_a_vivre,
                    score_faisabilite=score
                )
                resultats_list.append(resultat)

            # Generate IA explanation (use best scenario)
            best_result = resultats_list[1] if len(resultats_list) > 1 else resultats_list[0]

            ia_service = IAService(provider='groq')
            contexte = {
                'age': profil.age,
                'situation_familiale': profil.get_situation_familiale_display(),
                'type_contrat': profil.get_type_contrat_display(),
                'revenus_mensuels': float(profil.revenus_mensuels),
                'charges_totales': float(profil.charges_totales),
                'taux_endettement_actuel': float(profil.taux_endettement_actuel),
                'reste_a_vivre_avant': 0,
                'type_credit': simulation.get_type_credit_display(),
                'montant_souhaite': float(projet.montant_souhaite),
                'duree_mois': projet.duree_mois,
                'apport_personnel': float(projet.apport_personnel),
                'taux_utilise': float(best_result.taux_utilise),
                'mensualite': float(best_result.mensualite),
                'cout_total': float(best_result.cout_total),
                'taux_endettement_nouveau': float(best_result.taux_endettement_nouveau),
                'reste_a_vivre': float(best_result.reste_a_vivre),
                'score_faisabilite': best_result.score_faisabilite
            }

            explication_data = ia_service.generer_explication(contexte)
            ExplicationIA.objects.create(
                simulation=simulation,
                **explication_data
            )

            # Update status
            simulation.statut = 'TERMINEE'
            simulation.save()

            return Response(
                SimulationDetailSerializer(simulation).data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            simulation.statut = 'ERREUR'
            simulation.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Generate PDF report."""
        # TODO: Implement PDF generation
        return Response({'message': 'PDF generation not yet implemented'})

    @action(detail=True, methods=['post'])
    def email(self, request, pk=None):
        """Send results by email."""
        # TODO: Implement email sending
        return Response({'message': 'Email sending not yet implemented'})


class OffreBancaireViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Bank offers API endpoint (read-only).

    GET /api/simulation/offres-bancaires/ - List all active offers
    """

    queryset = OffreBancaire.objects.filter(actif=True)
    serializer_class = OffreBancaireSerializer
    filterset_fields = ['type_credit', 'banque']
