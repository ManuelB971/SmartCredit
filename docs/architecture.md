# Architecture du Projet Smart Crédit

## Vue d'ensemble

Smart Crédit est une application Django 5.x basée sur une architecture classique MVT (Model-View-Template) avec API REST intégrée.

```
smart-credit/
├── backend/                    # Code serveur Django
│   ├── smart_credit/           # Projet Django principal
│   ├── simulation/             # App centrale (modèles, logique métier)
│   ├── users/                  # Authentification
│   └── notifications/          # Emails et PDF
├── frontend/                   # Templates HTML + assets statiques
├── docs/                       # Documentation technique
└── scripts/                    # Utilitaires
```

## Modèles de données

### Utilisateur (simulation.models.Utilisateur)
- Extends Django AbstractUser
- Champs: email, first_name, last_name, phone, situation_familiale
- Lien: 1 utilisateur ↔ N simulations

### Simulation (simulation.models.Simulation)
- Clé primaire: id
- Champs: type_credit, statut, utilisateur_id, date_creation
- États: CREEE, EN_COURS, TERMINEE, ERREUR

### ProfilFinancier (simulation.models.ProfilFinancier)
- Relation: 1 Simulation ↔ 1 ProfilFinancier
- Données personnelles: age, situation_familiale, ville
- Données financières: revenus_mensuels, charges*

### ProjetCredit (simulation.models.ProjetCredit)
- Relation: 1 Simulation ↔ 1 ProjetCredit
- Champs: montant_souhaite, duree_mois, apport_personnel

### OffreBancaire (simulation.models.OffreBancaire)
- Taux par banque/type/durée
- Mise à jour mensuelle manuelle

### ResultatSimulation (simulation.models.ResultatSimulation)
- 1 Simulation ↔ 3 ResultatSimulation (3 scénarios)
- Résultats calculés: mensualite, cout_total, score_faisabilite

### ExplicationIA (simulation.models.ExplicationIA)
- Explication générée par IA
- Champs: texte, recommandations, avertissements, temps_generation_ms

## Flux de données

```
1. Utilisateur → Formulaire (3 étapes)
2. → API POST /simulations/
3. → Création Simulation + ProfilFinancier + ProjetCredit
4. → API POST /simulations/{id}/calcul/
5. → CalculService.calculer_*()
6. → ScoringService.calculer_score()
7. → IAService.generer_explication()
8. → Création 3x ResultatSimulation + ExplicationIA
9. → Frontend affiche résultats
```

## Services métier

### CalculService
- `calculer_mensualite(capital, taux, duree)` → Decimal
- `calculer_cout_total(mensualite, duree, capital)` → Decimal
- `calculer_taux_endettement(charges, revenus)` → Decimal
- `calculer_reste_a_vivre(revenus, charges, mensualite)` → Decimal

### ScoringService
- `calculer_score(profil, resultats)` → int (0-100)
- Facteurs: endettement, reste à vivre, emploi, apport, âge

### IAService
- `generer_explication(contexte)` → dict
- Provider: Groq (recommandé) ou HuggingFace
- Fallback: Explication mock en développement

## API Endpoints

```
POST   /api/simulation/simulations/                     # Créer simulation
GET    /api/simulation/simulations/{id}/                # Get détail
POST   /api/simulation/simulations/{id}/calcul/         # Lancer calcul
POST   /api/simulation/simulations/{id}/email/          # Envoyer email
GET    /api/simulation/offres-bancaires/                # Lister taux
POST   /api/users/register/                             # Register
POST   /api/users/login/                                # Login
GET    /api/users/me/                                   # Profil
GET    /api/users/simulations/                          # Historique
```

## Dépendances clés

- **Django 5.x** - Framework web
- **DRF (3.15+)** - API REST
- **PostgreSQL 16** - Base de données
- **django-cors-headers** - CORS
- **django-filter** - Filtrage API
- **groq** (optionnel) - API IA ultra-rapide
- **WeasyPrint** (optionnel) - Génération PDF

## Sécurité

- Authentification: Token-based (optionnel pour simulations publiques)
- HTTPS obligatoire en production
- CSRF protection (natif Django)
- SQL injection prevention (ORM)
- Rate limiting: À implémenter
- Validation: Strict sur tous les champs financiers

## Performance

- Cache queries: À implémenter
- Async tasks: À implémenter (Celery)
- CDN static files: Production
- Database indexes sur: (type_credit, actif), (utilisateur_id), (date_creation)
