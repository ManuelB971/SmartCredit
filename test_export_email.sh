#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"
PASS="${PASS:-motdepassefort}"
EMAIL_DEST="${EMAIL_DEST:-destinataire@example.com}"
EMAIL="export_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> 0) Migrations + seed"
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py seed_offres || true

echo ""
echo "==> 1) Register: $EMAIL"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"nom\":\"Test\",\"prenom\":\"Export\"}" \
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
echo "==> 3) Create simulation IMMOBILIER"
SIM_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{
    "type_credit":"IMMOBILIER",
    "profil_financier":{
      "age":32,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Paris",
      "revenus_mensuels":"3500.00","autres_revenus":"0.00",
      "charges_logement":"750.00","charges_credits":"150.00","autres_charges":"0.00",
      "type_contrat":"CDI","anciennete_emploi_mois":36
    },
    "projet_credit":{
      "type_credit":"IMMOBILIER","montant_souhaite":"250000.00",
      "duree_mois":240,"apport_personnel":"30000.00"
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
echo "==> 4) POST /api/simulations/$SIM_ID/export-email/ — cas nominal"
curl -sS -X POST "$BASE/api/simulations/$SIM_ID/export-email/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL_DEST\"}" | python -m json.tool

echo ""
echo "==> 5) Export sans email — doit retourner 400"
curl -sS -X POST "$BASE/api/simulations/$SIM_ID/export-email/" \
  -H "Content-Type: application/json" \
  -d '{}' | python -m json.tool

echo ""
echo "==> 6) Export simulation inexistante — doit retourner 404"
curl -sS -X POST "$BASE/api/simulations/999999/export-email/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL_DEST\"}" | python -m json.tool

echo ""
echo "==> OK test_export_email terminé (compte: $EMAIL / $PASS)"
