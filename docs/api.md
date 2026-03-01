# Référence API Smart Crédit

## 1. Simulations

### Créer une simulation
```bash
POST /api/simulation/simulations/
Content-Type: application/json

{
  "type_credit": "IMMOBILIER",
  "profil_financier": {
    "age": 32,
    "situation_familiale": "CELIBATAIRE",
    "ville": "Paris",
    "revenus_mensuels": 3500.00,
    "charges_logement": 750.00,
    "charges_credits": 150.00,
    "charges_autres": 0.00,
    "type_contrat": "CDI",
    "anciennete_emploi_mois": 36
  },
  "projet_credit": {
    "montant_souhaite": 250000.00,
    "duree_mois": 240,
    "apport_personnel": 30000.00
  }
}
```

**Réponse (201 Created):**
```json
{
  "id": 42,
  "type_credit": "IMMOBILIER",
  "statut": "CREEE",
  "profil_financier": {...},
  "projet_credit": {...},
  "resultats": [],
  "explication_ia": null,
  "date_creation": "2026-03-01T10:30:00Z"
}
```

### Obtenir une simulation
```bash
GET /api/simulation/simulations/{id}/
```

### Lancer le calcul IA
```bash
POST /api/simulation/simulations/{id}/calcul/
```

**Réponse:**
```json
{
  "id": 42,
  "statut": "TERMINEE",
  "resultats": [
    {
      "scenario": "EQUILIBRE",
      "taux_utilise": 3.31,
      "mensualite": 1419.00,
      "cout_total": 90560.00,
      "taux_endettement_nouveau": 27.8,
      "reste_a_vivre": 1681.00,
      "score_faisabilite": 85,
      "offre_bancaire": {
        "id": 5,
        "banque": "Pretto",
        "type_credit": "IMMOBILIER",
        "taux_interet": 3.31
      }
    }
  ],
  "explication_ia": {
    "texte": "Votre taux d'endettement de 27,8% est excellent...",
    "recommandations": "Vous pourriez envisager...",
    "avertissements": null,
    "temps_generation_ms": 1250
  }
}
```

### Envoyer par email
```bash
POST /api/simulation/simulations/{id}/email/

{
  "email": "utilisateur@exemple.com"
}
```

## 2. Utilisateurs

### Inscription
```bash
POST /api/users/register/

{
  "email": "user@exemple.com",
  "password": "SecurePassword123!",
  "first_name": "Jean",
  "last_name": "Dupont"
}
```

**Réponse (201):**
```json
{
  "user": {
    "id": 1,
    "email": "user@exemple.com",
    "first_name": "Jean",
    "last_name": "Dupont"
  },
  "token": "a1b2c3d4e5f6g7h8i9j0..."
}
```

### Connexion
```bash
POST /api/users/login/

{
  "email": "user@exemple.com",
  "password": "SecurePassword123!"
}
```

### Profil utilisateur
```bash
GET /api/users/me/
Authorization: Token a1b2c3d4e5f6g7h8i9j0...
```

### Historique simulations
```bash
GET /api/users/simulations/
Authorization: Token a1b2c3d4e5f6g7h8i9j0...
```

## 3. Offres bancaires

### Lister toutes les offres
```bash
GET /api/simulation/offres-bancaires/
```

### Filtrer par type
```bash
GET /api/simulation/offres-bancaires/?type_credit=IMMOBILIER&banque=Pretto
```

**Réponse:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 5,
      "banque": "Pretto",
      "type_credit": "IMMOBILIER",
      "taux_interet": 3.31,
      "duree_min_mois": 60,
      "duree_max_mois": 360,
      "montant_max": null,
      "actif": true
    }
  ]
}
```

## Codes d'erreur

| Code | Signification |
|------|---------------|
| 400 | Validation échouée (données invalides) |
| 401 | Non authentifié |
| 403 | Forbidhidden (accès refusé) |
| 404 | Ressource non trouvée |
| 500 | Erreur serveur |

## Usage Limits (à implémenter)

- 10 simulations/heure pour guest
- 100 simulations/jour pour utilisateur
- Temps de réponse IA: < 3 secondes (Groq)
