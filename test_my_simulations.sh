#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"
PASS="${PASS:-motdepassefort}"
EMAIL="mysim_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> 0) Migrations + seed"
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py seed_offres || true

echo ""
echo "==> 1) Register: $EMAIL"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"nom\":\"Test\",\"prenom\":\"Historique\"}" \
  | python -m json.tool

echo "==> 2) JWT token"
TOKENS="$(curl -sS -X POST "$BASE/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")"
export TOKENS
ACCESS="$(python - <<'PY'
import json, os
print(json.loads(os.environ["TOKENS"])["access"])
PY
)"
AUTH="Authorization: Bearer $ACCESS"

echo ""
echo "==> 3) GET /api/users/me/simulations/ — historique vide"
curl -sS "$BASE/api/users/me/simulations/" -H "$AUTH" | python -m json.tool

echo ""
echo "==> 4) Create simulation ETUDIANT"
SIM_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{
    "type_credit":"ETUDIANT",
    "profil_financier":{
      "age":21,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Paris",
      "revenus_mensuels":"500.00","autres_revenus":"0.00",
      "charges_logement":"300.00","charges_credits":"0.00","autres_charges":"50.00",
      "type_contrat":"ETUDIANT","anciennete_emploi_mois":0
    },
    "projet_credit":{
      "type_credit":"ETUDIANT","montant_souhaite":"20000.00",
      "duree_mois":60,"apport_personnel":"0.00"
    }
  }')"
export SIM="$SIM_JSON"
SIM_ID="$(python - <<'PY'
import json, os
print(json.loads(os.environ["SIM"])["simulation_id"])
PY
)"
echo "Simulation id: $SIM_ID"

echo ""
echo "==> 5) GET /api/users/me/simulations/ — doit contenir la simulation"
curl -sS "$BASE/api/users/me/simulations/" -H "$AUTH" | python -m json.tool

echo ""
echo "==> 6) GET /api/users/me/simulations/ SANS token — doit retourner 401"
curl -sS "$BASE/api/users/me/simulations/" | python -m json.tool

echo ""
echo "==> OK test_my_simulations terminé (compte: $EMAIL / $PASS)"
