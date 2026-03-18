import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    Simulation,
    ProfilFinancier,
    ProjetCredit,
    OffreBancaire,
    ResultatSimulation,
    ExplicationIA,
    TypeCredit,
    StatutSimulation,
    ScenarioResultat,
)
from .utils import mensualite as calc_mensualite, cout_total as calc_cout_total, taux_endettement as calc_te


def _json_body(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


def _to_decimal(value, default="0"):
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


@csrf_exempt
@require_http_methods(["POST"])
def create_simulation(request: HttpRequest):
    data = _json_body(request)
    type_credit = data.get("type_credit")
    profil = data.get("profil_financier") or {}
    projet = data.get("projet_credit") or {}

    if type_credit not in (TypeCredit.ETUDIANT, TypeCredit.IMMOBILIER):
        return JsonResponse({"error": "type_credit invalide"}, status=400)

    simulation = Simulation.objects.create(
        type_credit=type_credit,
        statut=StatutSimulation.EN_COURS,
        utilisateur=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
    )

    ProfilFinancier.objects.create(
        simulation=simulation,
        age=int(profil.get("age") or 18),
        situation_familiale=str(profil.get("situation_familiale") or "AUTRE"),
        nombre_enfants=int(profil.get("nombre_enfants") or 0),
        ville=profil.get("ville") or None,
        revenus_mensuels=_to_decimal(profil.get("revenus_mensuels"), "0"),
        autres_revenus=_to_decimal(profil.get("autres_revenus"), "0"),
        charges_logement=_to_decimal(profil.get("charges_logement"), "0"),
        charges_credits=_to_decimal(profil.get("charges_credits"), "0"),
        autres_charges=_to_decimal(profil.get("autres_charges"), "0"),
        type_contrat=profil.get("type_contrat") or None,
        anciennete_emploi_mois=profil.get("anciennete_emploi_mois") or None,
    )

    ProjetCredit.objects.create(
        simulation=simulation,
        type_credit=type_credit,
        montant_souhaite=_to_decimal(projet.get("montant_souhaite"), "0"),
        duree_mois=int(projet.get("duree_mois") or 1),
        apport_personnel=_to_decimal(projet.get("apport_personnel"), "0"),
    )

    return JsonResponse({"simulation_id": simulation.id})


@require_http_methods(["GET"])
def get_simulation(request: HttpRequest, simulation_id: int):
    try:
        sim = Simulation.objects.select_related("profil_financier", "projet_credit").get(id=simulation_id)
    except Simulation.DoesNotExist:
        return JsonResponse({"error": "Simulation introuvable"}, status=404)

    payload = {
        "id": sim.id,
        "type_credit": sim.type_credit,
        "date_simulation": sim.date_simulation.isoformat(),
        "statut": sim.statut,
        "utilisateur_id": sim.utilisateur_id,
        "profil_financier": {
            "age": sim.profil_financier.age,
            "situation_familiale": sim.profil_financier.situation_familiale,
            "nombre_enfants": sim.profil_financier.nombre_enfants,
            "ville": sim.profil_financier.ville,
            "revenus_mensuels": str(sim.profil_financier.revenus_mensuels),
            "autres_revenus": str(sim.profil_financier.autres_revenus),
            "charges_logement": str(sim.profil_financier.charges_logement),
            "charges_credits": str(sim.profil_financier.charges_credits),
            "autres_charges": str(sim.profil_financier.autres_charges),
            "type_contrat": sim.profil_financier.type_contrat,
            "anciennete_emploi_mois": sim.profil_financier.anciennete_emploi_mois,
        },
        "projet_credit": {
            "type_credit": sim.projet_credit.type_credit,
            "montant_souhaite": str(sim.projet_credit.montant_souhaite),
            "duree_mois": sim.projet_credit.duree_mois,
            "apport_personnel": str(sim.projet_credit.apport_personnel),
        },
        "resultats": [
            {
                "id": r.id,
                "scenario": r.scenario,
                "mensualite": str(r.mensualite),
                "taux_utilise": str(r.taux_utilise),
                "cout_total": str(r.cout_total),
                "taux_endettement": str(r.taux_endettement),
                "reste_a_vivre": str(r.reste_a_vivre) if r.reste_a_vivre is not None else None,
                "score_faisabilite": r.score_faisabilite,
                "offre_bancaire_id": r.offre_bancaire_id,
            }
            for r in sim.resultats.order_by("date_calcul")
        ],
        "explication_ia": getattr(sim, "explication_ia", None) and {
            "texte_explication": sim.explication_ia.texte_explication,
            "recommandations": sim.explication_ia.recommandations,
            "avertissements": sim.explication_ia.avertissements,
            "niveau_langage": sim.explication_ia.niveau_langage,
        },
    }
    return JsonResponse(payload)


@csrf_exempt
@require_http_methods(["POST"])
def calculate_simulation(request: HttpRequest, simulation_id: int):
    try:
        sim = Simulation.objects.select_related("profil_financier", "projet_credit").get(id=simulation_id)
    except Simulation.DoesNotExist:
        return JsonResponse({"error": "Simulation introuvable"}, status=404)

    # Offres éligibles (type + durée dans l'intervalle)
    offres = list(
        OffreBancaire.objects.select_related("banque")
        .filter(type_credit=sim.type_credit, duree_min_mois__lte=sim.projet_credit.duree_mois, duree_max_mois__gte=sim.projet_credit.duree_mois)
        .order_by("taux_annuel")
    )
    if not offres:
        return JsonResponse({"error": "Aucune offre bancaire disponible pour ces paramètres"}, status=409)

    # Trois scénarios simples (min / median / max)
    offers_for_scenarios = {
        ScenarioResultat.PRUDENT: offres[0],
        ScenarioResultat.EQUILIBRE: offres[len(offres) // 2],
        ScenarioResultat.CONFORT: offres[-1],
    }

    capital = sim.projet_credit.montant_souhaite - sim.projet_credit.apport_personnel
    if capital <= 0:
        return JsonResponse({"error": "Montant emprunté invalide (montant - apport <= 0)"}, status=400)

    revenus = sim.profil_financier.revenus_mensuels + sim.profil_financier.autres_revenus
    charges_existantes = sim.profil_financier.charges_logement + sim.profil_financier.charges_credits + sim.profil_financier.autres_charges

    ResultatSimulation.objects.filter(simulation=sim).delete()

    results_payload = []
    for scenario, offre in offers_for_scenarios.items():
        taux_decimal = Decimal(offre.taux_annuel) / Decimal(100)  # 3.31 -> 0.0331
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
        results_payload.append({"id": r.id, "scenario": scenario, "offre": {"banque": offre.banque.nom, "taux": str(offre.taux_annuel)}})

    sim.statut = StatutSimulation.TERMINEE
    sim.save(update_fields=["statut"])

    ExplicationIA.objects.update_or_create(
        simulation=sim,
        defaults={
            "texte_explication": "Votre simulation a été calculée à partir de vos revenus, charges et projet. Les taux sont indicatifs à date de mise à jour.",
            "recommandations": "Réduire les charges, augmenter l'apport ou ajuster la durée peut améliorer le dossier.",
            "avertissements": "Ce résultat ne constitue pas une offre contractuelle d'une banque.",
        },
    )

    return JsonResponse({"ok": True, "resultats": results_payload})


@login_required
@require_http_methods(["GET"])
def my_simulations(request: HttpRequest):
    sims = (
        Simulation.objects.filter(utilisateur=request.user)
        .order_by("-date_simulation")
        .values("id", "type_credit", "date_simulation", "statut")
    )
    return JsonResponse({"simulations": list(sims)})


@require_http_methods(["GET"])
def list_offres(request: HttpRequest):
    type_credit = request.GET.get("type_credit")
    qs = OffreBancaire.objects.select_related("banque").all()
    if type_credit in (TypeCredit.ETUDIANT, TypeCredit.IMMOBILIER):
        qs = qs.filter(type_credit=type_credit)
    payload = [
        {
            "id": o.id,
            "banque": o.banque.nom,
            "type_credit": o.type_credit,
            "duree_min_mois": o.duree_min_mois,
            "duree_max_mois": o.duree_max_mois,
            "taux_annuel": str(o.taux_annuel),
            "date_mise_a_jour": o.date_mise_a_jour.isoformat(),
        }
        for o in qs.order_by("banque__nom", "taux_annuel")[:500]
    ]
    return JsonResponse({"offres": payload})

