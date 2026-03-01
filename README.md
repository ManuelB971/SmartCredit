#  Smart Crédit — Simulateur de Crédit Intelligent

<div align="center">

![Smart Crédit Banner](https://img.shields.io/badge/Smart%20Crédit-MVP1-0066FF?style=for-the-badge&logo=data:image/svg+xml;base64,...)

[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=flat-square&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/Licence-Académique-lightgrey?style=flat-square)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-En%20développement-yellow?style=flat-square)]()

> **Projet académique ECE Paris Tech**  
> Trouvez le meilleur taux pour votre crédit en 3 minutes grâce à l'IA.

</div>

---

## 📋 Table des matières

- [À propos](#-à-propos)
- [Fonctionnalités](#-fonctionnalités)
- [Stack technique](#-stack-technique)
- [Architecture du projet](#-architecture-du-projet)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Base de données](#-base-de-données)
- [Intégration IA](#-intégration-ia)
- [Lancer le projet](#-lancer-le-projet)
- [Déploiement](#-déploiement)
- [Parcours utilisateur](#-parcours-utilisateur)
- [API Reference](#-api-reference)
- [Tests](#-tests)
- [Planning & Sprints](#-planning--sprints)
- [Équipe](#-équipe)
- [Mentions légales](#-mentions-légales)

---

## 🎯 À propos

**Smart Crédit** est un simulateur de crédit en ligne boosté à l'intelligence artificielle qui facilite la compréhension des démarches d'obtention de crédit et aide les utilisateurs à trouver le meilleur taux disponible sur le marché français, de manière personnalisée et pédagogique.

### Problématique adressée

Les utilisateurs français rencontrent plusieurs difficultés lors de la recherche d'un crédit :

- ❌ Manque de clarté sur les critères d'éligibilité et les démarches
- ❌ Difficulté à comparer les offres entre différentes banques
- ❌ Incompréhension des calculs de taux, mensualités et coût total
- ❌ Absence de recommandations personnalisées pour améliorer leur dossier

### Types de crédits couverts (MVP1)

| Type | Détails |
|------|---------|
| 🎓 **Crédit étudiant** | Taux 0,80 % à 2,50 % — Montants jusqu'à 75 000 € — Différé possible |
| 🏠 **Crédit immobilier** | Taux 3,20 % à 3,70 % — Durée jusqu'à 25 ans — Taux d'endettement max 35 % |

---

## ✨ Fonctionnalités

### Must Have (MVP1)

- [x] Saisie guidée des informations personnelles (âge, situation familiale, ville)
- [x] Calcul automatique du taux d'endettement et du reste à vivre
- [x] Simulation de mensualité, taux et coût total du crédit
- [x] Score IA de faisabilité du dossier (0–100)
- [x] Explication personnalisée en langage naturel générée par l'IA
- [x] Comparaison de 3 scénarios : Prudent / Équilibré / Confortable
- [x] Export du récapitulatif en PDF envoyé par email
- [x] Formulaire de contact pour être recontacté par un conseiller
- [x] Création de compte optionnelle + historique des simulations

### Règles métier implémentées

```
Taux d'endettement = (Charges mensuelles / Revenus mensuels) × 100  ≤ 35%
Reste à vivre = Revenus − Charges − Nouvelle mensualité             ≥ 800€ (seul) / 1 200€ (couple)
Mensualité    = Capital × (t/12) / (1 − (1 + t/12)^-n)
Coût total    = (Mensualité × n) − Capital emprunté
```

---

## 🛠 Stack technique

### Backend

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Framework web | Django | 5.x |
| API REST | Django REST Framework | 3.15+ |
| Base de données | PostgreSQL | 16 |
| Serveur WSGI | Gunicorn | 21.x |
| Proxy inverse | Nginx | 1.24 |
| Génération PDF | WeasyPrint / ReportLab | latest |
| Envoi d'emails | Django Email + SMTP | natif |

### Frontend

| Composant | Technologie |
|-----------|-------------|
| Template UI | Tabler Admin (Bootstrap 5) |
| JavaScript | Vanilla JS + Alpine.js |
| Interactions | AJAX (fetch API) |
| Responsive | Mobile-first (50/50) |

### Intelligence Artificielle

| Option | Description | Statut |
|--------|-------------|--------|
| **Groq API** | Inférence ultra-rapide, plan gratuit généreux | ✅ Recommandé |
| Hugging Face Inference API | Modèles open-source (Mistral 7B, Llama 3) | ✅ Alternative |
| Ollama (local) | Gratuit, nécessite GPU | 🔧 Optionnel |

Orchestration IA via **LangChain**.

### Hébergement

```
VPS Hostinger — Ubuntu Server 22.04 LTS
SSL/TLS : Let's Encrypt (certbot)
```

---

## 🏗 Architecture du projet

```
smart-credit/
│
├── backend/
│   ├── smart_credit/              # Projet Django principal
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── simulation/                # App principale
│   │   ├── models.py              # Utilisateur, Simulation, ProfilFinancier...
│   │   ├── views.py               # Vues API et templates
│   │   ├── serializers.py         # DRF serializers
│   │   ├── urls.py
│   │   ├── services/
│   │   │   ├── calculs.py         # Moteur de calcul financier
│   │   │   ├── scoring.py         # Score de faisabilité IA
│   │   │   └── ia_service.py      # Intégration Groq/HuggingFace
│   │   └── migrations/
│   │
│   ├── users/                     # Authentification & comptes
│   ├── notifications/             # Emails & PDF
│   └── requirements.txt
│
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── wizard/
│   │   │   ├── step1_profil.html
│   │   │   ├── step2_revenus.html
│   │   │   ├── step3_projet.html
│   │   │   └── step4_loading.html
│   │   └── results/
│   │       ├── results.html
│   │       └── comparison.html
│   └── static/
│       ├── css/
│       ├── js/
│       └── img/
│
├── docs/                          # Documentation technique
│   ├── architecture.md
│   ├── api.md
│   └── uml/
│
├── scripts/                       # Utilitaires déploiement
│   ├── deploy.sh
│   └── backup.sh
│
├── docker-compose.yml             # Dev environment (optionnel)
├── .env.example
├── manage.py
└── README.md
```

---

## 🚀 Installation

### Prérequis

- Python 3.11+
- Node.js 18+ (pour les assets frontend)
- PostgreSQL 16
- Git

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-org/smart-credit.git
cd smart-credit
```

### 2. Créer l'environnement virtuel Python

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# ou
venv\Scripts\activate           # Windows
```

### 3. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos valeurs (voir section Configuration)
```

### 5. Créer la base de données PostgreSQL

```bash
psql -U postgres
CREATE DATABASE smart_credit_db;
CREATE USER smart_credit_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE smart_credit_db TO smart_credit_user;
\q
```

### 6. Appliquer les migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Charger les données initiales (taux bancaires)

```bash
python manage.py loaddata fixtures/offres_bancaires.json
```

### 8. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

---

## ⚙️ Configuration

### Fichier `.env`

```env
# Django
SECRET_KEY=votre_secret_key_django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DB_NAME=smart_credit_db
DB_USER=smart_credit_user
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# IA — Groq API (recommandé)
GROQ_API_KEY=votre_cle_groq
GROQ_MODEL=llama3-8b-8192

# IA — Hugging Face (alternative)
HF_API_KEY=votre_cle_huggingface
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_app

# PDF
PDF_STORAGE_PATH=media/pdf/
```

---

## 🗄 Base de données

### Schéma relationnel

```
utilisateurs (1) ──── (0..*) simulations
simulations  (1) ──── (1)    profils_financiers
simulations  (1) ──── (1)    projets_credit
simulations  (1) ──── (1..*) resultats_simulations
simulations  (1) ──── (0..1) explications_ia
offres_bancaires (1) ─ (0..*) resultats_simulations
```

### Principales tables

| Table | Description |
|-------|-------------|
| `utilisateurs` | Comptes utilisateurs (email, mot de passe hashé) |
| `simulations` | Entrée principale par simulation (type, statut, utilisateur lié) |
| `profils_financiers` | Revenus, charges, situation familiale, contrat |
| `projets_credit` | Montant, durée, apport personnel |
| `offres_bancaires` | Taux par banque, type de crédit, durée min/max |
| `resultats_simulations` | Mensualité, coût total, score faisabilité, scénario |
| `explications_ia` | Texte généré par l'IA, recommandations, avertissements |

### Taux bancaires — Données initiales (février 2026)

**Crédit Immobilier**

| Banque | 15 ans | 20 ans | 25 ans |
|--------|--------|--------|--------|
| Pretto | 3,20 % | 3,31 % | 3,40 % |
| Boursorama | 3,25 % | 3,35 % | 3,45 % |
| BNP Paribas | 3,40 % | 3,50 % | 3,60 % |
| Crédit Agricole | 3,50 % | 3,60 % | 3,70 % |

**Crédit Étudiant**

| Banque | Taux | Montant max |
|--------|------|-------------|
| BNP Paribas | 0,80 % | 75 000 € |
| Bpifrance (État) | 0,90 % | 20 000 € |
| Crédit Agricole | 0,99 % | 60 000 € |
| Banque Populaire | 1,50 % | 50 000 € |
| Crédit Mutuel | 1,50 % | 30 000 € |

> ⚠️ Les taux sont mis à jour **manuellement chaque mois** dans la table `offres_bancaires`.  
> Les résultats affichés sont **indicatifs** et ne constituent pas une offre contractuelle.

---

## 🤖 Intégration IA

### Fonctionnement

L'IA intervient après la saisie du formulaire pour :

1. **Analyser** la situation financière (revenus, charges, endettement)
2. **Calculer** le score de faisabilité (0–100)
3. **Identifier** le meilleur taux parmi le panel de banques
4. **Générer** une explication personnalisée en langage naturel
5. **Proposer** des recommandations actionnables

### Prompt Engineering — Exemple

```python
SYSTEM_PROMPT = """
Tu es un conseiller financier pédagogique et bienveillant spécialisé dans les crédits français.
Analyse la situation de l'utilisateur et génère une explication en 3 à 5 phrases maximum.
Ton : {ton}  (tutoiement pour étudiants, vouvoiement pour crédit immobilier)
Niveau : accessible (bac général)
Ne sois jamais décourageant. Finis toujours sur une note constructive.
"""

USER_PROMPT = """
Profil : {age} ans, {situation_familiale}, {type_contrat}
Revenus nets : {revenus} €/mois
Charges actuelles : {charges} €/mois
Taux d'endettement actuel : {taux_endettement} %
Reste à vivre estimé : {reste_a_vivre} €
Type de crédit : {type_credit}
Montant souhaité : {montant} €
Score de faisabilité calculé : {score}/100

Génère l'explication personnalisée et 2-3 recommandations concrètes.
"""
```

### Seuils d'alerte automatiques

```python
if taux_endettement > 35:
    → Alerte rouge : "Risque de sur-endettement"

if reste_a_vivre < 800 and situation == "CELIBATAIRE":
    → Alerte orange : "Reste à vivre insuffisant"

if reste_a_vivre < 1200 and situation in ["MARIE", "PACSE"]:
    → Alerte orange : "Reste à vivre insuffisant pour un couple"
```

---

## ▶️ Lancer le projet

### Serveur de développement

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer Django
python manage.py runserver

# L'application est disponible sur http://localhost:8000
```

### Avec Docker (optionnel)

```bash
docker-compose up --build
# Application : http://localhost:8000
# pgAdmin    : http://localhost:5050
```

---

## 🌐 Déploiement

### VPS Hostinger — Ubuntu 22.04

#### 1. Préparer le serveur

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx postgresql certbot python3-certbot-nginx -y
```

#### 2. Configurer Nginx

```nginx
server {
    listen 80;
    server_name smartcredit.fr www.smartcredit.fr;

    location /static/ {
        alias /var/www/smart-credit/staticfiles/;
    }

    location /media/ {
        alias /var/www/smart-credit/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 3. Activer SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d smartcredit.fr -d www.smartcredit.fr
```

#### 4. Configurer Gunicorn comme service

```bash
# /etc/systemd/system/smart-credit.service
[Unit]
Description=Smart Crédit — Gunicorn daemon
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/smart-credit
ExecStart=/var/www/smart-credit/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    smart_credit.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable smart-credit
sudo systemctl start smart-credit
```

#### 5. Collecter les fichiers statiques

```bash
python manage.py collectstatic --noinput
```

---

## 🗺 Parcours utilisateur

```
1. Page d'accueil          → CTA "Simuler mon crédit"
         ↓
2. Choix type de crédit    → Étudiant | Immobilier
         ↓
3. Wizard Étape 1/3        → Profil (âge, situation, ville)
         ↓
4. Wizard Étape 2/3        → Revenus & Charges
         ↓
5. Wizard Étape 3/3        → Projet (montant, durée, apport)
         ↓
6. Loader IA (~2s)         → Analyse en cours...
         ↓
7. Résultats               → Taux, mensualité, score, explication IA
         ↓
8. Comparaison scénarios   → Prudent | Équilibré | Confortable
         ↓
9. Capture lead            → Email → Envoi PDF automatique
         ↓
10. Création compte (opt.) → Historique des simulations
```

---

## 📡 API Reference

### Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/simulations/` | Créer une nouvelle simulation |
| `GET` | `/api/simulations/{id}/` | Récupérer une simulation |
| `POST` | `/api/simulations/{id}/calcul/` | Lancer le calcul IA |
| `GET` | `/api/simulations/{id}/pdf/` | Générer le PDF |
| `POST` | `/api/simulations/{id}/email/` | Envoyer les résultats par email |
| `GET` | `/api/offres-bancaires/` | Lister les taux disponibles |
| `POST` | `/api/auth/register/` | Créer un compte |
| `POST` | `/api/auth/login/` | Connexion |
| `GET` | `/api/users/me/simulations/` | Historique utilisateur |

### Exemple — Lancer une simulation

**Requête**
```json
POST /api/simulations/
{
  "type_credit": "IMMOBILIER",
  "profil": {
    "age": 32,
    "situation_familiale": "CELIBATAIRE",
    "ville": "Paris",
    "revenus_mensuels": 3500,
    "charges_logement": 750,
    "charges_credits": 150,
    "type_contrat": "CDI",
    "anciennete_emploi_mois": 36
  },
  "projet": {
    "montant_souhaite": 250000,
    "duree_mois": 240,
    "apport_personnel": 30000
  }
}
```

**Réponse**
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
      "taux_endettement": 27.8,
      "reste_a_vivre": 1681.00,
      "score_faisabilite": 85,
      "offre_bancaire": "Pretto"
    }
  ],
  "explication_ia": {
    "texte": "Votre taux d'endettement de 27,8 % est excellent et bien en dessous du plafond réglementaire. Votre CDI de 3 ans et votre apport de 30 000 € renforcent significativement votre dossier. Vous avez de très bonnes chances d'obtenir un financement dans les meilleures conditions du marché.",
    "recommandations": "Vous pourriez envisager d'augmenter votre apport à 35 000 € pour négocier un taux encore plus avantageux.",
    "avertissements": null
  }
}
```

---

## 🧪 Tests

### Lancer les tests

```bash
# Tous les tests
python manage.py test

# Tests par application
python manage.py test simulation
python manage.py test users

# Avec couverture
pip install coverage
coverage run manage.py test
coverage report
coverage html  # Rapport HTML dans htmlcov/
```

### Tests prioritaires

| Catégorie | Tests |
|-----------|-------|
| Calculs financiers | Mensualité, coût total, taux d'endettement (marge < 1 %) |
| Règles métier | Seuil 35 % endettement, reste à vivre minimum |
| API IA | Temps de réponse < 3 secondes, cohérence explication |
| Formulaire | Validation de tous les champs obligatoires |
| PDF | Génération et envoi email |
| Responsive | Mobile (375px) et desktop (1280px) |

---

## 📅 Planning & Sprints

### Sprint 2 semaines — Répartition des tâches

| Phase | Back-end (D1 & D2) | Front-end (D3 & D4) |
|-------|--------------------|---------------------|
| **Phase 1** (J1-J3) | D1 : Architecture Django + modèles `Utilisateur`, `ProfilFinancier` — D2 : Modèles `ProjetCredit`, `OffreBancaire` + fixtures taux | D3 : Setup Tabler Admin + layout responsive — D4 : Wizard étapes 1 & 2 |
| **Phase 2** (J4-J7) | D1 : Moteur de calcul financier (endettement, mensualités) — D2 : Intégration API IA + prompt engineering | D3 : Wizard étape 3 + validations JS — D4 : Écran loader animé IA |
| **Phase 3** (J8-J11) | D1 : Scoring faisabilité + scénarios — D2 : Génération PDF + système email | D3 : Écran résultats dynamiques — D4 : Module comparaison scénarios |
| **Phase 4** (J12-J14) | D1 : Authentification + historique — D2 : Déploiement VPS + SSL | D3 : Formulaire compte + historique — D4 : Optimisation responsive finale |

### KPI de validation

- [ ] ≥ 50 simulations réalisées (phase test)
- [ ] Taux de complétion du parcours > 60 %
- [ ] Taux de capture d'email > 40 %
- [ ] Note satisfaction > 4/5
- [ ] Temps de réponse IA < 3 secondes

---

## 👥 Équipe

| Membre | Rôle |
|--------|------|
| **Dominique HUANG** | Product Owner / Chef de projet |
| **Hugo Lavaud** | Développeur Back-end |
| **SEIBOU Naadjath** |  Développeur Front-end |
| **Manuel BASSIEN** |Développeur Back-end / IA  |
| **Rajaa LAKRA** | Développeur Front-end / Tests |

**Établissement :** ECE Paris DEVBANK 
**Promotion :** 2025–2026

### Outils de collaboration

- 📋 **Gestion de projet :** Notion (roadmap, suivi des tâches)
- 🔀 **Versioning :** Git + GitHub
- 💬 **Communication :** Discord
- 📄 **Documentation :** README.md + Wiki GitHub

---

## ⚠️ Mentions légales & RGPD

> **Ce projet est un simulateur académique à des fins pédagogiques uniquement.**  
> Les résultats fournis sont **indicatifs** et ne constituent en aucun cas une offre de crédit, un engagement contractuel, ni un conseil financier personnalisé.

### Conformité RGPD (Projet académique)

- Les données collectées sont utilisées **uniquement** dans le cadre de ce projet académique
- Aucune donnée bancaire sensible (IBAN, RIB) n'est collectée ni stockée
- Les données sont conservées pour la **durée du projet académique** uniquement
- Toute personne peut demander la **suppression de ses données** par email
- Les mots de passe sont **hashés** (Django natif — PBKDF2)

### Disclaimer

```
Smart Crédit n'est pas un intermédiaire en opérations bancaires (IOB).
Les taux affichés sont des moyennes de marché à date de mise à jour et peuvent varier.
Consultez toujours un conseiller bancaire agréé avant toute décision de financement.
```

---

## 📄 Licence

Projet académique — ECE Paris Tech— Version 1.0 — Février 2026  
Usage éducatif non commercial uniquement.

---

<div align="center">

**Smart Crédit** — *Trouvez le meilleur taux en 3 minutes* 

* ECE Paris Tech — Promotion 2025/2026*

</div>
