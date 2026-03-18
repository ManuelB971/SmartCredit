import json
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.credit.models import Banque, OffreBancaire, TypeCredit


class ApiFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        b = Banque.objects.create(nom="TestBank")
        OffreBancaire.objects.create(
            banque=b,
            type_credit=TypeCredit.IMMOBILIER,
            duree_min_mois=240,
            duree_max_mois=240,
            taux_annuel=3.31,
            date_mise_a_jour=date(2026, 2, 11),
        )

    def test_create_and_calculate_simulation(self):
        body = {
            "type_credit": "IMMOBILIER",
            "profil_financier": {
                "age": 32,
                "situation_familiale": "CELIBATAIRE",
                "revenus_mensuels": "3500",
                "autres_revenus": "0",
                "charges_logement": "750",
                "charges_credits": "150",
                "autres_charges": "0",
            },
            "projet_credit": {"montant_souhaite": "250000", "duree_mois": 240, "apport_personnel": "30000"},
        }
        resp = self.client.post("/api/simulations/", data=body, format="json")
        self.assertEqual(resp.status_code, 201)
        sim_id = resp.json().get("simulation_id")
        self.assertIsNotNone(sim_id)

        resp2 = self.client.post(f"/api/simulations/{sim_id}/calcul/", data={}, format="json")
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.json()["ok"])

        resp3 = self.client.get(f"/api/simulations/{sim_id}/")
        self.assertEqual(resp3.status_code, 200)
        payload = resp3.json()
        self.assertEqual(payload["id"], sim_id)
        self.assertTrue(len(payload["resultats"]) >= 1)

