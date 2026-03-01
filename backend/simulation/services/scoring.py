"""
Scoring service for feasibility scoring.
"""

from decimal import Decimal


class ScoringService:
    """
    Feasibility scoring engine (0-100).
    """

    @staticmethod
    def calculer_score(profil: dict, resultats: dict) -> int:
        """
        Calculate feasibility score based on multiple factors.

        Factors:
        - Debt ratio (35%): +15 to -30
        - Remaining money: +10 to -20
        - Employment: +10 to -10
        - Personal contribution: +5 to 0
        - Age factor: +5 to -5
        """
        score = 50  # Base score

        # Factor 1: Debt ratio (35% threshold)
        taux_endettement = resultats.get('taux_endettement_nouveau', 50)
        if taux_endettement <= 25:
            score += 15
        elif taux_endettement <= 35:
            score += 5
        elif taux_endettement <= 40:
            score -= 10
        else:
            score -= 30

        # Factor 2: Remaining money
        reste_a_vivre = resultats.get('reste_a_vivre', 0)
        if reste_a_vivre >= 2000:
            score += 10
        elif reste_a_vivre >= 1200:
            score += 5
        elif reste_a_vivre >= 800:
            score += 0
        elif reste_a_vivre > 0:
            score -= 10
        else:
            score -= 20

        # Factor 3: Employment stability
        type_contrat = profil.get('type_contrat', '')
        anciennete = profil.get('anciennete_emploi_mois', 0)

        if type_contrat == 'CDI':
            if anciennete >= 36:
                score += 10
            elif anciennete >= 24:
                score += 8
            elif anciennete >= 12:
                score += 5
            elif anciennete >= 3:
                score += 2
        elif type_contrat in ['ALTERNANCE', 'ASSIMILE_SALARIE']:
            if anciennete >= 12:
                score += 5
            else:
                score += 0
        elif type_contrat == 'TRAVAILLEUR_INDEPENDANT':
            if anciennete >= 36:
                score += 5
            else:
                score -= 5
        elif type_contrat in ['STAGE', 'CDD', 'SANS_EMPLOI']:
            score -= 10
        elif type_contrat == 'RETRAITE':
            score += 3

        # Factor 4: Personal contribution
        apport_ratio = resultats.get('apport_ratio', 0)  # apport / (apport + credit)
        if apport_ratio >= 0.20:  # 20%+
            score += 5
        elif apport_ratio >= 0.10:  # 10%+
            score += 2

        # Factor 5: Age factor
        age = profil.get('age', 40)
        if 25 <= age <= 50:
            score += 5
        elif 20 <= age < 25:
            score += 0
        elif 50 < age <= 65:
            score += 2
        elif age > 65:
            score -= 5

        # Clamp between 0-100
        return max(0, min(100, score))

    @staticmethod
    def get_score_interpretation(score: int) -> str:
        """Get textual interpretation of score."""
        if score >= 80:
            return "Excellent - Très bonnes chances de validation"
        elif score >= 60:
            return "Bon - Chances de validation"
        elif score >= 40:
            return "Acceptable - Possible avec négociation"
        elif score >= 20:
            return "Risqué - Validation difficile"
        else:
            return "Très risqué - Déconseillé"
