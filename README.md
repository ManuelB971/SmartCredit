# SmartCredit

## Démarrer (dev)

### Prérequis
- Docker + Docker Compose

### Variables d’environnement
Copie `.env.example` vers `.env` puis ajuste si besoin.

### Lancer Postgres + API Django

```bash
docker compose up -d db
docker compose up --build backend
```

### Connexion à la base PostgreSQL (SGBD)
Pour se connecter avec DBeaver / pgAdmin / DataGrip :
- **Host**: `localhost`
- **Port**: `5666`
- **Database**: `smartcredit`
- **User**: `smartcredit`
- **Password**: `smartcredit`

### Migrations

Dans un autre terminal :

```bash
docker compose exec backend python manage.py migrate
```

### Seed banques/offres

```bash
docker compose exec backend python manage.py seed_offres
```

### Activer l’IA locale (Ollama) (optionnel)
L’API peut générer un **score** + une **explication** via un modèle gratuit en local (Ollama).

1) Installer Ollama (macOS) : télécharger depuis `https://ollama.com/download` puis ouvrir l’app.

2) Vérifier que le service répond :

```bash
curl http://localhost:11434/api/tags
```

3) Télécharger un modèle (recommandé) :

```bash
ollama pull llama3.1:8b
```

Alternative plus léger :

```bash
ollama pull llama3.2:3b
```

4) Vérifier la configuration côté API (dans `.env`) :
- `OLLAMA_HOST=http://host.docker.internal:11434`
- `AI_MODEL=llama3.1:8b`
- `AI_TIMEOUT_SEC=6`

5) Tester le parcours complet avec IA :

```bash
chmod +x test_parcours_ia.sh
./test_parcours_ia.sh lea@example.com motdepassefort Dupont Lea
```

### Endpoints MVP (exemples)
- `POST /api/auth/register/`
- `POST /api/auth/token/` (JWT)
- `POST /api/auth/token/refresh/` (JWT)
- `POST /api/simulations/`
- `POST /api/simulations/{id}/calcul/`
- `GET /api/simulations/{id}/`
- `GET /api/users/me/simulations/`
- `POST /api/simulations/{id}/export-email/`
- `GET /api/offres/?type_credit=IMMOBILIER`

### Swagger + Auth (JWT)
1. Récupère un token: `POST /api/auth/token/` avec `{ "email": "...", "password": "..." }`
2. Dans Swagger (`/api/swagger/`) clique **Authorize** puis colle `Bearer <access>`