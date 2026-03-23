from __future__ import annotations

from datetime import date
from django.core.management.base import BaseCommand

from apps.credit.models import Banque, OffreBancaire, TypeCredit


class Command(BaseCommand):
    help = "Seed banques/offres réalistes pour la démonstration (MVP1)."

    def handle(self, *args, **options):
        maj = date(2026, 3, 1)

        banques_data = {
            "BNP Paribas":        "https://www.bnpparibas.fr",
            "Crédit Agricole":    "https://www.credit-agricole.fr",
            "Société Générale":   "https://www.societegenerale.fr",
            "Boursorama Banque":  "https://www.boursorama.com",
            "Banque Populaire":   "https://www.banquepopulaire.fr",
            "Crédit Mutuel":      "https://www.creditmutuel.fr",
            "Caisse d'Épargne":   "https://www.caisse-epargne.fr",
            "Pretto":             "https://www.pretto.fr",
            "Bpifrance":          "https://www.bpifrance.fr",
            "Hello Bank":         "https://www.hellobank.fr",
            "Fortuneo":           "https://www.fortuneo.fr",
            "ING":                "https://www.ing.fr",
            "LCL":                "https://www.lcl.com",
        }

        bank_objs: dict[str, Banque] = {}
        for nom, url in banques_data.items():
            bank_objs[nom], _ = Banque.objects.get_or_create(
                nom=nom, defaults={"site_url": url}
            )

        # ── Immobilier ────────────────────────────────────────────────────────
        # Format: (banque, [(duree_min, duree_max, taux), ...])
        # Taux barème mars 2026 (indicatifs). Rééquilibrés pour varier le "meilleur" selon la durée :
        # 84-120 mois: Hello Bank / Boursorama en tête ; 121-180: Fortuneo / Pretto ; 181-240: plusieurs au coude-à-coude
        immobilier = [
            ("BNP Paribas", [
                (84,  120, 3.050),
                (121, 180, 3.150),
                (181, 240, 3.310),
                (241, 300, 3.480),
            ]),
            ("Crédit Agricole", [
                (84,  120, 3.100),
                (121, 180, 3.250),
                (181, 240, 3.450),
                (241, 300, 3.650),
            ]),
            ("Société Générale", [
                (84,  120, 3.080),
                (121, 180, 3.200),
                (181, 240, 3.380),
                (241, 300, 3.550),
            ]),
            ("Boursorama Banque", [
                (84,  120, 2.990),   # 84-120: en tête avec Hello Bank
                (121, 180, 3.120),
                (181, 240, 3.220),
                (241, 300, 3.400),
            ]),
            ("Hello Bank", [
                (84,  120, 2.980),   # 84-120: meilleur taux court terme
                (121, 180, 3.110),
                (181, 240, 3.240),
                (241, 300, 3.420),
            ]),
            ("Fortuneo", [
                (84,  120, 3.030),
                (121, 180, 3.050),   # 121-180: en tête
                (181, 240, 3.180),
                (241, 300, 3.380),
            ]),
            ("ING", [
                (84,  120, 3.040),
                (121, 180, 3.130),
                (181, 240, 3.270),
                (241, 300, 3.450),
            ]),
            ("LCL", [
                (84,  120, 3.090),
                (121, 180, 3.240),
                (181, 240, 3.410),
                (241, 300, 3.580),
            ]),
            ("Banque Populaire", [
                (84,  120, 3.120),
                (121, 180, 3.280),
                (181, 240, 3.430),
                (241, 300, 3.600),
            ]),
            ("Crédit Mutuel", [
                (84,  120, 3.090),
                (121, 180, 3.220),
                (181, 240, 3.400),
                (241, 300, 3.570),
            ]),
            ("Caisse d'Épargne", [
                (84,  120, 3.130),
                (121, 180, 3.290),
                (181, 240, 3.460),
                (241, 300, 3.630),
            ]),
            ("Pretto", [
                (84,  120, 3.020),
                (121, 180, 3.060),   # 121-180: proche Fortuneo
                (181, 240, 3.170),   # 181-240: en tête
                (241, 300, 3.350),
            ]),
        ]

        # ── Étudiant ──────────────────────────────────────────────────────────
        # Taux préférentiels (taux fixe, sans différé pour simplification MVP1)
        etudiant = [
            ("BNP Paribas", [
                (12,  24,  0.800),
                (25,  60,  1.200),
                (61,  120, 1.900),
            ]),
            ("Crédit Agricole", [
                (12,  24,  0.990),
                (25,  60,  1.450),
                (61,  120, 2.100),
            ]),
            ("Société Générale", [
                (12,  24,  0.950),
                (25,  60,  1.380),
                (61,  120, 2.050),
            ]),
            ("LCL", [
                (12,  24,  1.020),
                (25,  60,  1.520),
                (61,  120, 2.180),
            ]),
            ("Banque Populaire", [
                (12,  24,  1.200),
                (25,  60,  1.700),
                (61,  120, 2.300),
            ]),
            ("Crédit Mutuel", [
                (12,  24,  1.100),
                (25,  60,  1.600),
                (61,  120, 2.200),
            ]),
            ("Bpifrance", [
                (12,  24,  0.900),   # prêt étudiant garanti État
                (25,  60,  1.300),
                (61,  120, 1.800),
            ]),
            ("Caisse d'Épargne", [
                (12,  24,  1.050),
                (25,  60,  1.550),
                (61,  120, 2.150),
            ]),
        ]

        created = 0

        def upsert_offre(nom_banque: str, type_credit: str, duree_min: int, duree_max: int, taux: float):
            nonlocal created
            banque = bank_objs[nom_banque]
            obj, was_created = OffreBancaire.objects.get_or_create(
                banque=banque,
                type_credit=type_credit,
                duree_min_mois=duree_min,
                duree_max_mois=duree_max,
                defaults={"taux_annuel": taux, "date_mise_a_jour": maj},
            )
            if not was_created:
                updated = False
                if float(obj.taux_annuel) != taux:
                    obj.taux_annuel = taux
                    updated = True
                if obj.date_mise_a_jour != maj:
                    obj.date_mise_a_jour = maj
                    updated = True
                if updated:
                    obj.save(update_fields=["taux_annuel", "date_mise_a_jour"])
            else:
                created += 1

        for banque, tranches in immobilier:
            for duree_min, duree_max, taux in tranches:
                upsert_offre(banque, TypeCredit.IMMOBILIER, duree_min, duree_max, taux)

        for banque, tranches in etudiant:
            for duree_min, duree_max, taux in tranches:
                upsert_offre(banque, TypeCredit.ETUDIANT, duree_min, duree_max, taux)

        total_offres = OffreBancaire.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed terminé. Offres créées : {created} | Total en base : {total_offres}"
            )
        )
