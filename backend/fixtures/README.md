#!/usr/bin/env python
"""
Fixtures for Smart Crédit — Bank offers data.

Load with: python manage.py loaddata fixtures/offres_bancaires.json
"""

# This file would contain JSON fixtures for bank offers
# Example structure:

[
  {
    "model": "simulation.OffreBancaire",
    "pk": 1,
    "fields": {
      "banque": "Pretto",
      "type_credit": "IMMOBILIER",
      "taux_interet": 3.20,
      "duree_min_mois": 60,
      "duree_max_mois": 360,
      "montant_max": null,
      "description": "Meilleur taux immobilier",
      "actif": true
    }
  }
]
