# Smart Crédit — Simulateur de crédit propulsé par l'IA

> Comparez les offres de **9 grandes banques françaises** en temps réel, obtenez un **score IA personnalisé** et découvrez 3 scénarios de financement en moins de 3 minutes.

---

## Stack technique

| Couche | Technologie |
|---|---|
| Backend | Django 5.0 · Django REST Framework 3.15 · PostgreSQL 16 |
| Authentification | JWT (SimpleJWT) · Sessions Django |
| IA | Ollama (llama3.1:8b) · fallback rule-based |
| Frontend | Tailwind CSS · Material Design 3 · Chart.js 4 · Vanilla JS |
| Conteneurisation | Docker · Docker Compose |
| Documentation API | drf-spectacular · Swagger UI · ReDoc |

---

## Architecture

```
SmartCredit/
├── backend/
│   ├── apps/
│   │   ├── accounts/     # Auth JWT + gestion utilisateurs
│   │   ├── credit/       # Simulation, calcul, offres bancaires
│   │   ├── ai/           # Client Ollama + prompts + fallback
│   │   └── exports/      # Traçabilité export PDF/email
│   ├── templates/        # UI Django (landing, wizard, résultats)
│   └── static/js/        # Logique wizard + appels API
├── docs/                 # ERD (Mermaid)
├── stitch_screens/       # Captures d'écran UI pour démo
├── docker-compose.yml
└── .env.example
```

### Flux de simulation

```
Étape 1 (profil) → Étape 2 (revenus) → Étape 3 (projet)
        ↓ POST /api/simulations/
        ↓ POST /api/simulations/{id}/calcul/
        ↓ Ollama score IA (ou fallback rule-based)
        ↓ 3 scénarios : PRUDENT · ÉQUILIBRÉ · CONFORT
        ↓ Tableau de bord + graphiques Chart.js
```

---

## Démarrage rapide

### 1. Prérequis

- Docker Desktop (v24+) + Docker Compose v2

### 2. Configuration

```bash
cp .env.example .env
```

Variables clés dans `.env` :

```env
POSTGRES_DB=smartcredit
POSTGRES_USER=smartcredit
POSTGRES_PASSWORD=smartcredit
DJANGO_SECRET_KEY=change-me-in-production
DJANGO_DEBUG=1
OLLAMA_HOST=http://host.docker.internal:11434   # optionnel
AI_MODEL=llama3.1:8b
```

### 3. Lancer les services

```bash
docker compose up -d db
docker compose up --build backend
```

### 4. Initialisation base de données

```bash
# Dans un autre terminal
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_offres
```

L'application est disponible sur → **http://localhost:8001**

---

## Activer l'IA locale (Ollama) — optionnel

L'API génère un **score 0–100** + une **explication personnalisée** via un LLM local.
Sans Ollama, le système bascule automatiquement en mode **rule-based** (fallback transparent).

```bash
# 1. Installer Ollama : https://ollama.com/download
# 2. Télécharger le modèle (≈4.7 Go)
ollama pull llama3.1:8b

# 3. Vérifier que le service répond
curl http://localhost:11434/api/tags
```

---

## Endpoints API

| Méthode | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Public | Inscription + liaison simulation anonyme |
| `POST` | `/api/auth/token/` | Public | Authentification JWT |
| `POST` | `/api/auth/token/refresh/` | Public | Rafraîchissement du token |
| `GET` | `/api/auth/me/` | JWT | Profil utilisateur courant |
| `POST` | `/api/simulations/` | Public | Créer une simulation (wizard étape 3) |
| `GET` | `/api/simulations/{id}/` | Public | Récupérer résultats + explication IA |
| `POST` | `/api/simulations/{id}/calcul/` | Public | Lancer le calcul + scoring IA |
| `GET` | `/api/users/me/simulations/` | JWT | Historique des simulations |
| `GET` | `/api/offres/?type_credit=IMMOBILIER` | Public | Offres bancaires filtrées |
| `POST` | `/api/simulations/{id}/export-email/` | Public | Demande export PDF (traçabilité) |

### Documentation interactive

| URL | Format |
|---|---|
| `/api/swagger/` | Swagger UI (OpenAPI 3.0) |
| `/api/redoc/` | ReDoc |

**Authentification Swagger** :
1. `POST /api/auth/token/` → copier `access`
2. Cliquer **Authorize** → coller `Bearer <access>`

---

## Modèle de données

```
Simulation (1) ──→ (1) ProfilFinancier
           (1) ──→ (1) ProjetCredit
           (1) ──→ (N) ResultatSimulation ──→ (1) OffreBancaire ──→ (1) Banque
           (1) ──→ (1) ExplicationIA
           (1) ──→ (N) ExportPdfEmail
```

### Scénarios calculés

| Scénario | Logique de sélection |
|---|---|
| **PRUDENT** | Taux le plus bas parmi les offres éligibles |
| **ÉQUILIBRÉ** | Taux médian — recommandé par l'IA |
| **CONFORT** | Taux le plus élevé — mensualités les plus faibles |

### Score IA (0–100)

Calculé par Ollama ou par règles :
- `−65 pts` si taux d'endettement > 35 %
- `−55 pts` si reste à vivre < 800 €/mois
- Génère : explication · recommandations · avertissements

---

## Banques référencées (seed)

| Banque | Immobilier | Étudiant |
|---|---|---|
| BNP Paribas | ✓ (4 tranches) | ✓ (3 tranches) |
| Crédit Agricole | ✓ (4 tranches) | ✓ (3 tranches) |
| Société Générale | ✓ (4 tranches) | — |
| Boursorama Banque | ✓ (4 tranches) | — |
| Banque Populaire | ✓ (4 tranches) | ✓ (3 tranches) |
| Crédit Mutuel | ✓ (4 tranches) | ✓ (3 tranches) |
| Caisse d'Épargne | ✓ (4 tranches) | ✓ (3 tranches) |
| Pretto | ✓ (4 tranches) | — |
| Bpifrance | — | ✓ (3 tranches) |

Taux indicatifs barème mars 2026 · mis à jour via `seed_offres`.

---

## Tests

```bash
# Parcours complet (nouveau utilisateur → simulation → calcul)
BASE=http://localhost:8001 ./test_parcours_new_user.sh

# Parcours avec IA Ollama
BASE=http://localhost:8001 ./test_parcours_ia.sh lea@example.com motdepassefort Dupont Lea

# Cas limites (404, offres manquantes, valeurs négatives)
BASE=http://localhost:8001 ./test_simulation_edge_cases.sh

# Tests unitaires calcul financier
docker compose exec backend python manage.py test apps.credit
```

11 scripts de test bash couvrent l'intégralité des endpoints.

---

## Connexion base de données

Pour DBeaver / pgAdmin / DataGrip :

```
Host     : localhost
Port     : 5666
Database : smartcredit
User     : smartcredit
Password : smartcredit
```

---

## Roadmap post-MVP1

- [ ] Génération PDF réelle (WeasyPrint) + envoi email (Celery + Redis)
- [ ] Dashboard utilisateur — historique et comparaison des simulations
- [ ] Consentements RGPD — liaison modèle `Consentement` au frontend
- [ ] Rate limiting (django-ratelimit) + HTTPS redirect
- [ ] CI/CD GitHub Actions (lint · tests · build Docker)
- [ ] Import CSV des taux bancaires (mise à jour automatique)
- [ ] Prise en charge du différé de remboursement (prêt étudiant)
