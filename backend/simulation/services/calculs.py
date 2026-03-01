"""
Services for simulation calculations and AI integration.
"""

from decimal import Decimal
from datetime import datetime
import time


class CalculService:
    """Financial calculation engine."""

    @staticmethod
    def calculer_mensualite(capital: Decimal, taux_annuel: Decimal, duree_mois: int) -> Decimal:
        """
        Calculate monthly payment for a loan.
        Formula: M = C * (t/12) / (1 - (1 + t/12)^-n)
        """
        if taux_annuel == 0:
            return capital / duree_mois

        taux_mensuel = taux_annuel / 100 / 12
        n = duree_mois

        mensualite = capital * (taux_mensuel / (1 - (1 + taux_mensuel) ** (-n)))
        return mensualite.quantize(Decimal('0.01'))

    @staticmethod
    def calculer_cout_total(mensualite: Decimal, duree_mois: int, capital: Decimal) -> Decimal:
        """
        Calculate total cost of loan.
        Formula: Coût total = (Mensualité × n) - Capital emprunté
        """
        cout_total = (mensualite * duree_mois) - capital
        return cout_total.quantize(Decimal('0.01'))

    @staticmethod
    def calculer_taux_endettement(charges_mensuelles: Decimal, revenus_mensuels: Decimal) -> Decimal:
        """
        Calculate debt ratio.
        Formula: Taux = (Charges / Revenus) × 100
        """
        if revenus_mensuels == 0:
            return Decimal('0')

        taux = (charges_mensuelles / revenus_mensuels) * 100
        return taux.quantize(Decimal('0.01'))

    @staticmethod
    def calculer_reste_a_vivre(revenus: Decimal, charges: Decimal, nouvelle_mensualite: Decimal) -> Decimal:
        """
        Calculate remaining money after all charges.
        Formula: Reste = Revenus - Charges - Nouvelle mensualité
        """
        reste = revenus - charges - nouvelle_mensualite
        return reste.quantize(Decimal('0.01'))

    @staticmethod
    def valider_eligibilite(taux_endettement: Decimal, reste_a_vivre: Decimal, situation_familiale: str) -> dict:
        """
        Check eligibility based on financial rules.

        Rules:
        - Debt ratio must be ≤ 35%
        - Minimum remaining money: 800€ (single) or 1200€ (couple)
        """
        errors = []
        warnings = []

        if taux_endettement > 35:
            errors.append("Risque de sur-endettement")

        min_reste_a_vivre = Decimal('1200') if situation_familiale in ['MARIE', 'PACSE'] else Decimal('800')
        if reste_a_vivre < min_reste_a_vivre:
            errors.append(f"Reste à vivre insuffisant (minimum {min_reste_a_vivre}€)")

        return {
            'eligible': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


class ScoringService:
    """Feasibility scoring engine."""

    @staticmethod
    def calculer_score(profil: dict, resultats: dict) -> int:
        """
        Calculate feasibility score (0-100) based on financial indicators.
        """
        score = 50  # Base score

        # Debt ratio impact (-30 to +15)
        taux_endettement = resultats.get('taux_endettement_nouveau', 50)
        if taux_endettement <= 25:
            score += 15
        elif taux_endettement <= 35:
            score += 5
        else:
            score -= 30

        # Remaining money impact (-20 to +10)
        reste_a_vivre = resultats.get('reste_a_vivre', 0)
        if reste_a_vivre >= 2000:
            score += 10
        elif reste_a_vivre >= 1200:
            score += 5
        elif reste_a_vivre < 800:
            score -= 20

        # Employment impact (-10 to +10)
        type_contrat = profil.get('type_contrat', '')
        anciennete = profil.get('anciennete_emploi_mois', 0)

        if type_contrat == 'CDI' and anciennete >= 24:
            score += 10
        elif type_contrat in ['CDI', 'ALTERNANCE'] and anciennete >= 12:
            score += 5
        elif type_contrat in ['STAGE', 'CDD']:
            score -= 10

        return max(0, min(100, score))  # Clamp between 0-100


class IAService:
    """AI integration service."""

    SYSTEM_PROMPT = """Tu es un conseiller financier pédagogique et bienveillant spécialisé dans les crédits français.
Analyse la situation de l'utilisateur et génère une explication en 3 à 5 phrases maximum.
Ton : {ton}
Niveau : accessible (bac général)
Ne sois jamais décourageant. Finis toujours sur une note constructive."""

    USER_PROMPT = """Profil : {age} ans, {situation_familiale}, {type_contrat}
Revenus nets : {revenus}€/mois
Charges actuelles : {charges}€/mois
Taux d'endettement actuel : {taux_endettement}%
Reste à vivre estimé : {reste_a_vivre}€
Type de crédit : {type_credit}
Montant souhaité : {montant}€
Taux appliqué : {taux}%
Mensualité : {mensualite}€
Taux d'endettement avec crédit : {taux_endettement_nouveau}%
Score de faisabilité calculé : {score}/100

Génère l'explication personnalisée et 2-3 recommandations concrètes."""

    @staticmethod
    def generer_explication(contexte: dict, provider: str = 'groq') -> dict:
        """
        Generate AI-powered explanation.

        Args:
            contexte: Dictionary with all relevant financial data
            provider: 'groq' or 'huggingface'

        Returns:
            dict with 'texte', 'recommandations', 'avertissements'
        """
        start_time = time.time()

        # For development: return mock response
        # In production: call Groq or HuggingFace API

        explication = {
            'texte': f"Votre taux d'endettement de {contexte.get('taux_endettement_nouveau', 0)}% est en dessous du plafond réglementaire. "
                    f"Avec une mensualité de {contexte.get('mensualite', 0)}€ et un reste à vivre de {contexte.get('reste_a_vivre', 0)}€, "
                    f"votre dossier présente de bonnes chances de financement.",
            'recommandations': "Vous pourriez envisager d'augmenter votre apport personnel pour négocier un meilleur taux.",
            'avertissements': None
        }

        temps_gen = int((time.time() - start_time) * 1000)
        explication['temps_generation_ms'] = temps_gen

        return explication

    @staticmethod
    def formater_prompt_system(ton: str) -> str:
        """Format system prompt with tone."""
        return IAService.SYSTEM_PROMPT.format(ton=ton)

    @staticmethod
    def formater_prompt_user(contexte: dict) -> str:
        """Format user prompt with context."""
        return IAService.USER_PROMPT.format(
            age=contexte.get('age'),
            situation_familiale=contexte.get('situation_familiale'),
            type_contrat=contexte.get('type_contrat'),
            revenus=contexte.get('revenus_mensuels'),
            charges=contexte.get('charges_totales'),
            taux_endettement=contexte.get('taux_endettement_actuel'),
            reste_a_vivre=contexte.get('reste_a_vivre_avant'),
            type_credit=contexte.get('type_credit'),
            montant=contexte.get('montant_souhaite'),
            taux=contexte.get('taux_utilise'),
            mensualite=contexte.get('mensualite'),
            taux_endettement_nouveau=contexte.get('taux_endettement_nouveau'),
            score=contexte.get('score_faisabilite')
        )
