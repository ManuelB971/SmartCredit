#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"
PASS="${PASS:-motdepassefort}"
NOM="${NOM:-Dupont}"
PRENOM="${PRENOM:-Lea}"

EMAIL="user_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> 0) Génération de données (profil + projet)"
if (( RANDOM % 2 == 0 )); then
  TYPE_CREDIT="IMMOBILIER"
  AGE=$((28 + RANDOM % 15))                       # 28-42
  SITUATION="$(printf '%s\n' CELIBATAIRE MARIE PACSE | awk "NR==$((1 + RANDOM % 3))")"
  VILLE="$(printf '%s\n' Paris Lyon Lille Bordeaux Nantes | awk "NR==$((1 + RANDOM % 5))")"
  REV=$((2800 + RANDOM % 2501))                   # 2800-5300
  AUTRES=$((RANDOM % 401))                        # 0-400
  LOGEMENT=$((500 + RANDOM % 701))                # 500-1200
  CREDITS=$((0 + RANDOM % 351))                   # 0-350
  AUTRES_CH=$((50 + RANDOM % 201))                # 50-250
  CONTRAT="$(printf '%s\n' CDI CDD FREELANCE | awk "NR==$((1 + RANDOM % 3))")"
  ANCIEN=$((6 + RANDOM % 85))                     # 6-90
  MONTANT=$((180000 + RANDOM % 221000))           # 180k-401k
  DUREE="$((180 + (RANDOM % 4) * 60))"            # 180/240/300/360
  APPORT=$((0 + RANDOM % 60001))                  # 0-60k
else
  TYPE_CREDIT="ETUDIANT"
  AGE=$((18 + RANDOM % 9))                        # 18-26
  SITUATION="CELIBATAIRE"
  VILLE="$(printf '%s\n' Paris Rennes Toulouse Grenoble Montpellier | awk "NR==$((1 + RANDOM % 5))")"
  REV=$((0 + RANDOM % 901))                       # 0-900
  AUTRES=$((0 + RANDOM % 301))                    # 0-300
  LOGEMENT=$((200 + RANDOM % 401))                # 200-600
  CREDITS=0
  AUTRES_CH=$((0 + RANDOM % 151))                 # 0-150
  CONTRAT="ETUDIANT"
  ANCIEN=0
  MONTANT=$((8000 + RANDOM % 42001))              # 8k-50k
  DUREE="$((24 + (RANDOM % 7) * 12))"             # 24..96
  APPORT=0
fi

echo "Type credit: $TYPE_CREDIT | age=$AGE | situation=$SITUATION | ville=$VILLE | revenus=$REV | logement=$LOGEMENT | credits=$CREDITS | montant=$MONTANT | duree_mois=$DUREE | apport=$APPORT"

echo "==> 1) (optionnel) migrations + seed"
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py seed_offres || true

echo "==> 2) Register (nouvel utilisateur): $EMAIL"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"nom\":\"$NOM\",\"prenom\":\"$PRENOM\"}" \
  | python3 -m json.tool

echo "==> 3) JWT token"
TOKENS="$(curl -sS -X POST "$BASE/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")"
export TOKENS
ACCESS="$(python3 - <<'PY'
import json, os
print(json.loads(os.environ["TOKENS"])["access"])
PY
)"
AUTH="Authorization: Bearer $ACCESS"

echo "==> 4) Create simulation"
SIM_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d "{
    \"type_credit\":\"$TYPE_CREDIT\",
    \"profil_financier\":{
      \"age\":$AGE,
      \"situation_familiale\":\"$SITUATION\",
      \"nombre_enfants\":0,
      \"ville\":\"$VILLE\",
      \"revenus_mensuels\":\"$REV.00\",
      \"autres_revenus\":\"$AUTRES.00\",
      \"charges_logement\":\"$LOGEMENT.00\",
      \"charges_credits\":\"$CREDITS.00\",
      \"autres_charges\":\"$AUTRES_CH.00\",
      \"type_contrat\":\"$CONTRAT\",
      \"anciennete_emploi_mois\":$ANCIEN
    },
    \"projet_credit\":{
      \"type_credit\":\"$TYPE_CREDIT\",
      \"montant_souhaite\":\"$MONTANT.00\",
      \"duree_mois\":$DUREE,
      \"apport_personnel\":\"$APPORT.00\"
    }
  }")"
export SIM="$SIM_JSON"
SIM_ID="$(python3 - <<'PY'
import json, os
print(json.loads(os.environ["SIM"])["simulation_id"])
PY
)"
echo "Simulation id: $SIM_ID"

echo "==> 5) Calculate"
curl -sS -X POST "$BASE/api/simulations/$SIM_ID/calcul/" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python3 -m json.tool

echo "==> 6) Details"
curl -sS "$BASE/api/simulations/$SIM_ID/" -H "$AUTH" | python3 -m json.tool

echo "==> OK (compte créé: $EMAIL / $PASS)"