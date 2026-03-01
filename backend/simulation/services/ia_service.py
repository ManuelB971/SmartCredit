"""
IA Service for AI-powered explanations and recommendations.
"""

import time
from typing import Optional
import os

# Try to import Groq, fallback to mock
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


class IAService:
    """
    AI integration service.
    Supports Groq API and HuggingFace as fallback.
    """

    SYSTEM_PROMPT_TEMPLATE = """Tu es un conseiller financier pédagogique et bienveillant spécialisé dans les crédits français.
Analyse la situation de l'utilisateur et génère une explication en 3 à 5 phrases maximum.
Ton : {ton}
Niveau : accessible (bac général, max bac+2)
Ne sois jamais décourageant. Finis toujours sur une note constructive.
Format:
1. Explication principale (2-3 phrases)
2. Recommandations (1-2 points clés)
3. Avertissements si nécessaire"""

    USER_PROMPT_TEMPLATE = """SITUATION FINANCIÈRE
Profil : {age} ans, {situation_familiale}, {type_contrat}
Revenus nets : {revenus_mensuels}€/mois
Charges actuelles : {charges_totales}€/mois
Taux d'endettement actuel : {taux_endettement_actuel:.1f}%
Reste à vivre estimé : {reste_a_vivre_avant}€

PROJET DE CRÉDIT
Type : {type_credit}
Montant souhaité : {montant_souhaite}€
Durée : {duree_mois} mois
Apport personnel : {apport_personnel}€

RÉSULTATS DE SIMULATION
Taux appliqué : {taux_utilise}%
Mensualité : {mensualite}€
Coût total du crédit : {cout_total}€
Taux d'endettement avec crédit : {taux_endettement_nouveau:.1f}%
Reste à vivre après crédit : {reste_a_vivre}€
Score de faisabilité : {score_faisabilite}/100

DEMANDE
Génère une explication personnalisée adaptée au profil et aux résultats, avec 2-3 recommandations concrètes et actionnables."""

    def __init__(self, provider: str = 'groq'):
        """
        Initialize IA service.

        Args:
            provider: 'groq' or 'huggingface'
        """
        self.provider = provider
        self.groq_client = None
        self.groq_model = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
        self.groq_api_key = os.getenv('GROQ_API_KEY')

        if HAS_GROQ and self.groq_api_key:
            self.groq_client = Groq(api_key=self.groq_api_key)

    def generer_explication(self, contexte: dict) -> dict:
        """
        Generate AI-powered explanation for simulation results.

        Args:
            contexte: Dictionary with all simulation data

        Returns:
            Dict with 'texte', 'recommandations', 'avertissements', 'temps_generation_ms'
        """
        start_time = time.time()

        try:
            if self.groq_client and self.provider == 'groq':
                result = self._generer_avec_groq(contexte)
            else:
                result = self._generer_mock(contexte)
        except Exception as e:
            result = self._generer_mock(contexte)

        temps_gen = int((time.time() - start_time) * 1000)
        result['temps_generation_ms'] = temps_gen

        return result

    def _generer_avec_groq(self, contexte: dict) -> dict:
        """Generate explanation using Groq API."""
        ton = "tutoiement" if contexte.get('type_credit') == 'ETUDIANT' else "vouvoiement"

        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(ton=ton)
        user_prompt = self.USER_PROMPT_TEMPLATE.format(**contexte)

        message = self.groq_client.messages.create(
            model=self.groq_model,
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        texte_complet = message.content[0].text

        # Parse response
        lines = texte_complet.split('\n')
        texte = '\n'.join([l for l in lines if l and not l.startswith(('1.', '2.', '3.'))])[:300]
        recommandations = '\n'.join([l for l in lines if l.startswith(('2.', 'Recommandation'))])[:200]
        avertissements = '\n'.join([l for l in lines if l.startswith(('3.', 'Avertissement'))])[:200]

        return {
            'texte': texte.strip(),
            'recommandations': recommandations.strip() or None,
            'avertissements': avertissements.strip() or None
        }

    def _generer_mock(self, contexte: dict) -> dict:
        """Generate mock explanation for development."""
        score = contexte.get('score_faisabilite', 50)
        taux_end = contexte.get('taux_endettement_nouveau', 30)
        reste_a_vivre = contexte.get('reste_a_vivre', 1500)
        type_credit = contexte.get('type_credit', 'IMMOBILIER')

        if score >= 80:
            texte = f"Votre dossier présente un excellent profil de financement. Un taux d'endettement de {taux_end:.1f}% significantly below seuil regulatory, " \
                   f"associé à un reste à vivre confortable de {reste_a_vivre}€, démontre la solidité de votre situation financière. " \
                   f"Vous avez de très bonnes chances d'obtenir un financement aux meilleures conditions du marché."
            recommandations = "• Vous pouvez explorer une durée plus courte pour réduire le coût total du crédit\n• Envisagez une augmentation d'apport pour meilleures négociation"
        elif score >= 60:
            texte = f"Votre profil est favorable pour l'obtention d'un crédit. Avec un taux d'endettement de {taux_end:.1f}% et un reste à vivre " \
                   f"de {reste_a_vivre}€, votre situation répond aux critères bancaires standards. Quelques optimisations pourraient renforcer votre dossier."
            recommandations = "• Augmentez légèrement votre apport personnel si possible\n• Envisagez une réduction des charges non-essentielles"
        else:
            texte = f"Votre taux d'endettement de {taux_end:.1f}% approche du seuil limite. Un travail sur vos charges ou une augmentation de revenus " \
                   f"pourrait améliorer significativement votre dossier. N'hésitez pas à consulter un conseiller pour optimiser votre situation."
            recommandations = "• Diminuez vos charges mensuelles pendant 3-6 mois avant le dépôt du dossier\n• Augmentez votre apport personnel autant que possible"

        avertissements = None
        if taux_end > 35:
            avertissements = "⚠️ Votre taux d'endettement dépasse le seuil réglementaire de 35%. Votre dossier sera difficile à valider."
        elif reste_a_vivre < 800:
            avertissements = "⚠️ Votre reste à vivre est très faible. Vérifiez que vous pouvez faire face à des dépenses imprévues."

        return {
            'texte': texte,
            'recommandations': recommandations,
            'avertissements': avertissements
        }

    @staticmethod
    def formater_contexte_pour_ia(profil, projet, resultats) -> dict:
        """Format all data for IA processing."""
        return {
            'age': profil.age,
            'situation_familiale': profil.get_situation_familiale_display(),
            'type_contrat': profil.get_type_contrat_display(),
            'revenus_mensuels': float(profil.revenus_mensuels),
            'charges_totales': float(profil.charges_totales),
            'taux_endettement_actuel': float(profil.taux_endettement_actuel),
            'reste_a_vivre_avant': float(Decimal('0')),  # Calculate if needed
            'type_credit': resultats.get('simulation').get_type_credit_display(),
            'montant_souhaite': float(projet.montant_souhaite),
            'duree_mois': projet.duree_mois,
            'apport_personnel': float(projet.apport_personnel),
            'taux_utilise': float(resultats.get('taux_utilise', 0)),
            'mensualite': float(resultats.get('mensualite', 0)),
            'cout_total': float(resultats.get('cout_total', 0)),
            'taux_endettement_nouveau': float(resultats.get('taux_endettement_nouveau', 0)),
            'reste_a_vivre': float(resultats.get('reste_a_vivre', 0)),
            'score_faisabilite': resultats.get('score_faisabilite', 0)
        }
