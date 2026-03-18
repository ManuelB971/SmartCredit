from __future__ import annotations

from datetime import date
from django.core.management.base import BaseCommand

from apps.credit.models import Banque, OffreBancaire, TypeCredit


class Command(BaseCommand):
    help = "Seed banques/offres de base (MVP1)."

    def handle(self, *args, **options):
        maj = date(2026, 2, 11)

        banques = {
            "Pretto": None,
            "Crédit Agricole": None,
            "Boursorama": None,
            "BNP Paribas": None,
            "Banque Populaire": None,
            "Crédit Mutuel": None,
            "Bpifrance": None,
        }

        bank_objs: dict[str, Banque] = {}
        for nom, url in banques.items():
            bank_objs[nom], _ = Banque.objects.get_or_create(nom=nom, defaults={"site_url": url})

        # Immobilier (annexe A, valeurs indicatives)
        immobilier = [
            ("Pretto", [(180, 3.200), (240, 3.310), (300, 3.400)]),
            ("Crédit Agricole", [(180, 3.500), (240, 3.600), (300, 3.700)]),
            ("Boursorama", [(180, 3.250), (240, 3.350), (300, 3.450)]),
            ("BNP Paribas", [(180, 3.400), (240, 3.500), (300, 3.600)]),
        ]

        # Étudiant (annexe A, valeurs indicatives)
        etudiant = [
            ("BNP Paribas", [(12, 0.800)]),
            ("Crédit Agricole", [(12, 0.990)]),
            ("Banque Populaire", [(12, 1.500)]),
            ("Crédit Mutuel", [(12, 1.500)]),
            ("Bpifrance", [(12, 0.900)]),
        ]

        created = 0

        def upsert_offre(nom_banque: str, type_credit: str, duree_mois: int, taux: float):
            nonlocal created
            banque = bank_objs[nom_banque]
            obj, was_created = OffreBancaire.objects.get_or_create(
                banque=banque,
                type_credit=type_credit,
                duree_min_mois=duree_mois,
                duree_max_mois=duree_mois,
                date_mise_a_jour=maj,
                defaults={"taux_annuel": taux},
            )
            if not was_created and obj.taux_annuel != taux:
                obj.taux_annuel = taux
                obj.save(update_fields=["taux_annuel"])
            if was_created:
                created += 1

        for banque, points in immobilier:
            for duree, taux in points:
                upsert_offre(banque, TypeCredit.IMMOBILIER, duree, taux)

        for banque, points in etudiant:
            for duree, taux in points:
                upsert_offre(banque, TypeCredit.ETUDIANT, duree, taux)

        self.stdout.write(self.style.SUCCESS(f"Seed terminé. Offres créées: {created}"))

