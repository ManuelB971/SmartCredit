import random
from decimal import Decimal

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Simulation,
    OffreBancaire,
    ResultatSimulation,
    ExplicationIA,
    StatutSimulation,
    ScenarioResultat,
    TypeCredit,
)
from .serializers import (
    SimulationCreateSerializer,
    SimulationDetailSerializer,
    OffreBancaireSerializer,
)
from .utils import mensualite as calc_mensualite, cout_total as calc_cout_total, taux_endettement as calc_te
from apps.ai.client import ollama_generate, OllamaError
from apps.ai.prompts import build_scoring_prompt
from apps.ai.schemas import parse_ai_json, AiParseError


@extend_schema(
    tags=["Simulations"],
    summary="Créer une simulation",
    request=SimulationCreateSerializer,
    responses={201: OpenApiResponse(description="Simulation créée (id)")},
    examples=[
        OpenApiExample(
            "Immobilier (exemple)",
            value={
                "type_credit": "IMMOBILIER",
                "profil_financier": {
                    "age": 32,
                    "situation_familiale": "CELIBATAIRE",
                    "nombre_enfants": 0,
                    "ville": "Paris",
                    "revenus_mensuels": "3500.00",
                    "autres_revenus": "0.00",
                    "charges_logement": "750.00",
                    "charges_credits": "150.00",
                    "autres_charges": "0.00",
                    "type_contrat": "CDI",
                    "anciennete_emploi_mois": 36,
                },
                "projet_credit": {
                    "type_credit": "IMMOBILIER",
                    "montant_souhaite": "250000.00",
                    "duree_mois": 240,
                    "apport_personnel": "30000.00",
                },
            },
            request_only=True,
        ),
        OpenApiExample(
            "Étudiant (exemple)",
            value={
                "type_credit": "ETUDIANT",
                "profil_financier": {
                    "age": 21,
                    "situation_familiale": "CELIBATAIRE",
                    "nombre_enfants": 0,
                    "ville": "Paris",
                    "revenus_mensuels": "500.00",
                    "autres_revenus": "0.00",
                    "charges_logement": "300.00",
                    "charges_credits": "0.00",
                    "autres_charges": "50.00",
                    "type_contrat": "ETUDIANT",
                    "anciennete_emploi_mois": 0,
                },
                "projet_credit": {
                    "type_credit": "ETUDIANT",
                    "montant_souhaite": "20000.00",
                    "duree_mois": 60,
                    "apport_personnel": "0.00",
                },
            },
            request_only=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def create_simulation(request):
    serializer = SimulationCreateSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    sim = serializer.save()
    return Response({"simulation_id": sim.id}, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Simulations"],
    summary="Récupérer une simulation (détails + résultats + explication IA)",
    responses={200: SimulationDetailSerializer, 404: OpenApiResponse(description="Simulation introuvable")},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_simulation(request, simulation_id: int):
    try:
        sim = (
            Simulation.objects.select_related("profil_financier", "projet_credit")
            .prefetch_related("resultats__offre_bancaire__banque")
            .get(id=simulation_id)
        )
    except Simulation.DoesNotExist:
        return Response({"error": "Simulation introuvable"}, status=404)

    return Response(SimulationDetailSerializer(sim).data)


@extend_schema(
    tags=["Simulations"],
    summary="Calculer une simulation (génère résultats/scénarios + score + explication IA)",
    description=(
        "Calcule les résultats (mensualité, coût total, taux d'endettement, reste à vivre) à partir des données saisies "
        "et des offres bancaires disponibles.\n\n"
        "IA (Ollama, optionnel):\n"
        "- Si `OLLAMA_HOST` est accessible, l'API tente de générer un `score_faisabilite` (0–100) + explication + recommandations.\n"
        "- En cas d'échec/timeout, l'API retombe sur un scoring par règles.\n\n"
        "La réponse inclut un objet `ai` indiquant `status` (`ok` ou `fallback`) et éventuellement `score`."
    ),
    responses={
        200: OpenApiResponse(description="Résultats générés"),
        400: OpenApiResponse(description="Paramètres invalides"),
        404: OpenApiResponse(description="Simulation introuvable"),
        409: OpenApiResponse(description="Aucune offre bancaire disponible"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def calculate_simulation(request, simulation_id: int):
    try:
        sim = Simulation.objects.select_related("profil_financier", "projet_credit").get(id=simulation_id)
    except Simulation.DoesNotExist:
        return Response({"error": "Simulation introuvable"}, status=404)

    offres = list(
        OffreBancaire.objects.select_related("banque")
        .filter(
            type_credit=sim.type_credit,
            duree_min_mois__lte=sim.projet_credit.duree_mois,
            duree_max_mois__gte=sim.projet_credit.duree_mois,
        )
        .order_by("taux_annuel")
    )
    if not offres:
        return Response({"error": "Aucune offre bancaire disponible pour ces paramètres"}, status=409)

    offers_for_scenarios = {
        ScenarioResultat.PRUDENT: offres[0],
        ScenarioResultat.EQUILIBRE: offres[len(offres) // 2],
        ScenarioResultat.CONFORT: offres[-1],
    }

    capital = sim.projet_credit.montant_souhaite - sim.projet_credit.apport_personnel
    if capital <= 0:
        return Response({"error": "Montant emprunté invalide (montant - apport <= 0)"}, status=400)

    revenus = sim.profil_financier.revenus_mensuels + sim.profil_financier.autres_revenus
    charges_existantes = sim.profil_financier.charges_logement + sim.profil_financier.charges_credits + sim.profil_financier.autres_charges

    ResultatSimulation.objects.filter(simulation=sim).delete()
    results_payload = []

    # Pré-calcul d'un scénario de référence (PRUDENT) pour l'IA.
    offre_ref = offers_for_scenarios[ScenarioResultat.PRUDENT]
    taux_ref_decimal = Decimal(offre_ref.taux_annuel) / Decimal(100)
    m_ref = calc_mensualite(capital=capital, taux_annuel=taux_ref_decimal, n_mois=sim.projet_credit.duree_mois)
    ct_ref = calc_cout_total(mensualite_val=m_ref, n_mois=sim.projet_credit.duree_mois, capital=capital)
    te_ref = calc_te(charges=charges_existantes + m_ref, revenus=revenus)
    rav_ref = revenus - charges_existantes - m_ref

    # IA (Ollama) — fallback si indispo
    ai_score: int | None = None
    ai_text: str | None = None
    ai_reco: str | None = None
    ai_warn: str | None = None
    ai_status = "fallback"
    ai_error: str | None = None
    try:
        prompt = build_scoring_prompt(
            {
                "type_credit": sim.type_credit,
                "duree_mois": sim.projet_credit.duree_mois,
                "montant_souhaite": str(sim.projet_credit.montant_souhaite),
                "apport_personnel": str(sim.projet_credit.apport_personnel),
                "capital_emprunte": str(capital),
                "revenus": str(revenus),
                "charges_existantes": str(charges_existantes),
                "taux_endettement_ref": str(te_ref),
                "reste_a_vivre_ref": str(rav_ref),
                "mensualite_ref": str(m_ref),
                "cout_total_ref": str(ct_ref),
                "offre_ref": {
                    "banque": offre_ref.banque.nom,
                    "taux_annuel": str(offre_ref.taux_annuel),
                    "date_mise_a_jour": offre_ref.date_mise_a_jour.isoformat(),
                },
            }
        )
        raw = ollama_generate(prompt)
        decision = parse_ai_json(raw)
        ai_score = decision.score_faisabilite
        ai_text = decision.texte_explication
        ai_reco = decision.recommandations
        ai_warn = decision.avertissements
        ai_status = "ok"
    except (OllamaError, AiParseError) as e:
        ai_status = "fallback"
        ai_error = str(e)[:400]

    for scenario, offre in offers_for_scenarios.items():
        taux_decimal = Decimal(offre.taux_annuel) / Decimal(100)
        m = calc_mensualite(capital=capital, taux_annuel=taux_decimal, n_mois=sim.projet_credit.duree_mois)
        ct = calc_cout_total(mensualite_val=m, n_mois=sim.projet_credit.duree_mois, capital=capital)
        te = calc_te(charges=charges_existantes + m, revenus=revenus)
        rav = revenus - charges_existantes - m

        score = None
        if revenus > 0:
            score = 100
            if te > Decimal("35.00"):
                score = 35
            if rav < Decimal("800.00"):
                score = min(score, 45)
        if ai_score is not None:
            score = ai_score

        r = ResultatSimulation.objects.create(
            simulation=sim,
            offre_bancaire=offre,
            scenario=scenario,
            mensualite=m,
            taux_utilise=offre.taux_annuel,
            cout_total=ct,
            taux_endettement=te,
            reste_a_vivre=rav if rav >= 0 else Decimal("0.00"),
            score_faisabilite=score,
        )
        results_payload.append(
            {
                "id": r.id,
                "scenario": scenario,
                "offre": {"id": offre.id, "banque": offre.banque.nom, "taux_annuel": str(offre.taux_annuel)},
            }
        )

    sim.statut = StatutSimulation.TERMINEE
    sim.save(update_fields=["statut"])

    te_val = float(te_ref)
    rav_val = float(rav_ref)
    taux_str = str(offre_ref.taux_annuel).replace(".", ",")

    if te_val > 40 and rav_val < 1000:
        explications = [
            f"Votre taux d'endettement ({te_val:.1f} %) et votre reste à vivre ({rav_val:.0f} €) rendent le dossier délicat. "
            f"Parmi les offres comparées, le meilleur taux trouvé est de {taux_str} %. Une consolidation du dossier serait bénéfique.",
            f"Avec {te_val:.1f} % d'endettement et environ {rav_val:.0f} € de reste à vivre, les banques pourraient être exigeantes. "
            f"Nous avons identifié des offres à partir de {taux_str} %. Des ajustements sont possibles.",
        ]
    elif te_val > 35:
        explications = [
            f"Votre taux d'endettement ({te_val:.1f} %) frôle la limite habituelle des 35 %. "
            f"Reste à vivre : environ {rav_val:.0f} €. Le meilleur taux parmi les offres analysées : {taux_str} %.",
            f"Dossier à la limite : {te_val:.1f} % d'endettement, reste à vivre {rav_val:.0f} €. "
            f"Les offres les plus compétitives démarrent à {taux_str} %. Un peu plus d'apport ou une durée plus longue pourrait aider.",
        ]
    else:
        explications = [
            f"Votre profil est cohérent : taux d'endettement autour de {te_val:.1f} %, reste à vivre d'environ {rav_val:.0f} €. "
            f"Parmi les offres comparées, nous avons trouvé des taux à partir de {taux_str} %.",
            f"Les chiffres sont encourageants — endettement à {te_val:.1f} %, reste à vivre ~{rav_val:.0f} €. "
            f"Votre meilleure option parmi nos partenaires affiche un taux de {taux_str} %. Les taux restent indicatifs.",
        ]
    fallback_text = random.choice(explications)

    if te_val > 35 or rav_val < 800:
        reco_list = [
            "Augmentez l'apport personnel pour réduire le capital emprunté et rassurer les banques.",
            "Envisagez d'allonger la durée du crédit pour diminuer la mensualité et le taux d'endettement.",
            "Réduisez les charges existantes si possible (rachat de crédits, renégociation) avant de reposter.",
        ]
    else:
        reco_list = [
            "Comparez les offres détaillées auprès de nos partenaires pour affiner votre choix.",
            "Un courtier ou votre banque pourra valider ces taux et finaliser votre dossier.",
        ]
    fallback_reco = random.choice(reco_list)

    fallback_warn = "Ce résultat est indicatif et ne constitue pas une offre contractuelle. Consultez un conseiller pour valider votre situation."

    ExplicationIA.objects.update_or_create(
        simulation=sim,
        defaults={
            "texte_explication": ai_text or fallback_text,
            "recommandations": ai_reco or fallback_reco,
            "avertissements": ai_warn or fallback_warn,
        },
    )

    return Response(
        {"ok": True, "resultats": results_payload, "ai": {"status": ai_status, "score": ai_score, "error": ai_error}}
    )


@extend_schema(
    tags=["Simulations"],
    summary="Historique des simulations (utilisateur connecté)",
    responses={200: OpenApiResponse(description="Liste des simulations"), 401: OpenApiResponse(description="Non authentifié")},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_simulations(request):
    sims = (
        Simulation.objects.filter(utilisateur=request.user)
        .order_by("-date_simulation")
        .values("id", "type_credit", "date_simulation", "statut")
    )
    return Response({"simulations": list(sims)})


@extend_schema(
    tags=["Offres"],
    summary="Lister les offres bancaires (taux indicatifs)",
    description=(
        "Retourne les offres bancaires indicatives (annexe du cahier des charges) filtrables par `type_credit`.\n\n"
        "- Les taux sont **indicatifs** et datés via `date_mise_a_jour`.\n"
        "- Le filtre `type_credit` accepte `ETUDIANT` ou `IMMOBILIER`.\n"
        "- La liste est limitée à 500 entrées."
    ),
    responses={200: OffreBancaireSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def list_offres(request):
    type_credit = request.query_params.get("type_credit")
    qs = OffreBancaire.objects.select_related("banque").all()
    if type_credit in (TypeCredit.ETUDIANT, TypeCredit.IMMOBILIER):
        qs = qs.filter(type_credit=type_credit)
    qs = qs.order_by("banque__nom", "taux_annuel")[:500]
    return Response(OffreBancaireSerializer(qs, many=True).data)

