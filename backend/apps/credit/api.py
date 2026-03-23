from decimal import Decimal

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

# Villes en zone tendue (PTZ, Action Logement, etc.)
_ZONES_TENDUES = ("paris", "lyon", "marseille", "bordeaux", "toulouse", "lille", "nice", "nantes", "strasbourg", "montpellier")


def _ville_zone_tendue(ville: str | None) -> bool:
    if not ville or not ville.strip():
        return False
    v = ville.strip().lower()
    return any(z in v for z in _ZONES_TENDUES)
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.db.models import Prefetch

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
            .prefetch_related(
                Prefetch(
                    "resultats",
                    queryset=ResultatSimulation.objects.select_related("simulation__projet_credit").prefetch_related(
                        "offre_bancaire__banque"
                    ),
                )
            )
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

    # Sélection avec banques distinctes : PRUDENT = meilleur taux, EQUILIBRE = 2e banque distincte, CONFORT = 3e ou dernière
    seen_banques = set()
    selected = []
    for o in offres:
        bid = o.banque_id
        if bid not in seen_banques:
            seen_banques.add(bid)
            selected.append(o)
            if len(selected) >= 3:
                break
    if len(selected) == 1:
        selected.append(offres[len(offres) // 2] if len(offres) > 1 else offres[0])
    if len(selected) == 2:
        selected.append(offres[-1] if offres[-1] not in selected else offres[len(offres) // 2])
    offers_for_scenarios = {
        ScenarioResultat.PRUDENT: selected[0],
        ScenarioResultat.EQUILIBRE: selected[1] if len(selected) > 1 else offres[len(offres) // 2],
        ScenarioResultat.CONFORT: selected[2] if len(selected) > 2 else offres[-1],
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

    # Pré-calcul des 3 scénarios pour offres_comparees
    offres_comparees = []
    for scenario, offre in offers_for_scenarios.items():
        taux_d = Decimal(offre.taux_annuel) / Decimal(100)
        m = calc_mensualite(capital=capital, taux_annuel=taux_d, n_mois=sim.projet_credit.duree_mois)
        ct = calc_cout_total(mensualite_val=m, n_mois=sim.projet_credit.duree_mois, capital=capital)
        offres_comparees.append({
            "scenario": scenario,
            "banque": offre.banque.nom,
            "taux_annuel": str(offre.taux_annuel),
            "mensualite": round(float(m), 2),
            "cout_total_interets": round(float(ct), 2),
        })

    # IA (Ollama) — fallback si indispo
    ai_score: int | None = None
    ai_text: str | None = None
    ai_reco: str | None = None
    ai_warn: str | None = None
    ai_resume = ""
    ai_donnees: dict = {}
    ai_status = "fallback"
    ai_error: str | None = None
    try:
        montant_f_ref = float(sim.projet_credit.montant_souhaite)
        apport_ratio_pct = round(float(sim.projet_credit.apport_personnel) / montant_f_ref * 100, 1) if montant_f_ref > 0 else 0
        prompt = build_scoring_prompt(
            {
                "type_credit": sim.type_credit,
                "duree_mois": sim.projet_credit.duree_mois,
                "duree_annees": round(sim.projet_credit.duree_mois / 12, 1),
                "montant_souhaite": str(sim.projet_credit.montant_souhaite),
                "apport_personnel": str(sim.projet_credit.apport_personnel),
                "apport_ratio_pct": apport_ratio_pct,
                "capital_emprunte": str(capital),
                "revenus_mensuels_nets": str(revenus),
                "charges_existantes": str(charges_existantes),
                "taux_endettement_pct": round(float(te_ref), 2),
                "reste_a_vivre_mensuel": round(float(rav_ref), 2),
                "mensualite_prudent": round(float(m_ref), 2),
                "cout_total_interets_prudent": round(float(ct_ref), 2),
                "age": sim.profil_financier.age,
                "situation_familiale": sim.profil_financier.situation_familiale,
                "nombre_enfants": sim.profil_financier.nombre_enfants,
                "type_contrat": sim.profil_financier.type_contrat,
                "anciennete_emploi_mois": sim.profil_financier.anciennete_emploi_mois,
                "ville": sim.profil_financier.ville or "",
                "zone_tendue": _ville_zone_tendue(sim.profil_financier.ville),
                "meilleur_taux_disponible": str(offre_ref.taux_annuel),
                "offres_comparees": offres_comparees,
            }
        )
        raw = ollama_generate(prompt)
        decision = parse_ai_json(raw)
        ai_score = decision.score_faisabilite
        ai_text = decision.texte_explication
        ai_reco = decision.recommandations
        ai_warn = decision.avertissements
        ai_resume = decision.resume_executif or ""
        ai_donnees = {
            "points_forts_dossier": decision.points_forts_dossier,
            "risques_identifies": decision.risques_identifies,
            "prochaines_etapes": decision.prochaines_etapes,
        }
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

        score = 0
        if revenus > 0:
            te_f = float(te)
            rav_f = float(rav)
            score = 100
            # Taux d'endettement
            if te_f > 40:
                score -= 55
            elif te_f > 35:
                score -= 40
            elif te_f > 33:
                score -= 20
            elif te_f > 28:
                score -= 8
            # Reste à vivre
            if rav_f < 600:
                score -= 30
            elif rav_f < 800:
                score -= 20
            elif rav_f < 1000:
                score -= 10
            elif rav_f < 1200:
                score -= 4
            # Apport personnel
            montant_f = float(sim.projet_credit.montant_souhaite)
            if montant_f > 0:
                apport_ratio = float(sim.projet_credit.apport_personnel) / montant_f
                if apport_ratio < 0.05:
                    score -= 12
                elif apport_ratio < 0.10:
                    score -= 7
                elif apport_ratio < 0.20:
                    score -= 3
            # Stabilité professionnelle
            if sim.profil_financier.type_contrat in ("CDD", "INDEPENDANT"):
                score -= 8
            anc = sim.profil_financier.anciennete_emploi_mois
            if anc < 6:
                score -= 8
            elif anc < 24:
                score -= 4
            score = max(5, min(100, score))
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
        fallback_text = (
            f"Votre taux d'endettement ({te_val:.1f} %) et votre reste à vivre ({rav_val:.0f} €) rendent le dossier délicat. "
            f"Parmi les offres comparées, le meilleur taux trouvé est de {taux_str} %. Une consolidation du dossier serait bénéfique."
        )
    elif te_val > 35:
        fallback_text = (
            f"Votre taux d'endettement ({te_val:.1f} %) frôle la limite habituelle des 35 %. "
            f"Reste à vivre : environ {rav_val:.0f} €. Le meilleur taux parmi les offres analysées : {taux_str} %."
        )
    else:
        fallback_text = (
            f"Votre profil est cohérent : taux d'endettement autour de {te_val:.1f} %, reste à vivre d'environ {rav_val:.0f} €. "
            f"Parmi les offres comparées, nous avons trouvé des taux à partir de {taux_str} %."
        )

    if te_val > 35 or rav_val < 800:
        fallback_reco = "Augmentez l'apport personnel ou allongez la durée du crédit pour réduire votre taux d'endettement."
    else:
        fallback_reco = "Comparez les offres détaillées auprès de nos partenaires pour affiner votre choix. Un courtier peut également valider votre dossier."

    fallback_warn = "Ce résultat est indicatif et ne constitue pas une offre contractuelle. Consultez un conseiller pour valider votre situation."

    ExplicationIA.objects.update_or_create(
        simulation=sim,
        defaults={
            "texte_explication": ai_text or fallback_text,
            "recommandations": ai_reco or fallback_reco,
            "avertissements": ai_warn or fallback_warn,
            "resume_executif": ai_resume,
            "donnees_enrichies": ai_donnees,
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

