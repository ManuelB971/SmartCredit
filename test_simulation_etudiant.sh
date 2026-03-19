#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"
PASS="${PASS:-motdepassefort}"

echo "==> 0) Migrations + seed"
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py seed_offres || true

echo ""
echo "======================================================"
echo " CAS 1 — ETUDIANT standard (Paris, 500 revenus, 20k, 60 mois)"
echo "======================================================"

EMAIL="etu_cas1_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> Register: $EMAIL"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"nom\":\"Leroy\",\"prenom\":\"Emma\"}" \
  | python -m json.tool

echo "==> JWT token"
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

echo "==> Create simulation ETUDIANT (21 ans, Paris, 500 revenus, 20k)"
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

echo "==> Calculate"
curl -sS -X POST "$BASE/api/simulations/$SIM_ID/calcul/" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> Details (PRUDENT / EQUILIBRE / CONFORT)"
curl -sS "$BASE/api/simulations/$SIM_ID/" -H "$AUTH" | python -m json.tool

echo "==> OK CAS 1 (compte: $EMAIL / $PASS)"

echo ""
echo "======================================================"
echo " CAS 2 — ETUDIANT avec job (Lyon, 700+200 revenus, 35k, 84 mois)"
echo "======================================================"

EMAIL2="etu_cas2_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> Register: $EMAIL2"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL2\",\"password\":\"$PASS\",\"nom\":\"Moreau\",\"prenom\":\"Tom\"}" \
  | python -m json.tool

echo "==> JWT token"
TOKENS2="$(curl -sS -X POST "$BASE/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL2\",\"password\":\"$PASS\"}")"
export TOKENS2
ACCESS2="$(python - <<'PY'
import json, os
print(json.loads(os.environ["TOKENS2"])["access"])
PY
)"
AUTH2="Authorization: Bearer $ACCESS2"

echo "==> Create simulation ETUDIANT (23 ans, Lyon, job etudiant, 35k)"
SIM2_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH2" \
  -d '{
    "type_credit":"ETUDIANT",
    "profil_financier":{
      "age":23,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Lyon",
      "revenus_mensuels":"700.00","autres_revenus":"200.00",
      "charges_logement":"400.00","charges_credits":"0.00","autres_charges":"80.00",
      "type_contrat":"ETUDIANT","anciennete_emploi_mois":0
    },
    "projet_credit":{
      "type_credit":"ETUDIANT","montant_souhaite":"35000.00",
      "duree_mois":84,"apport_personnel":"0.00"
    }
  }')"
export SIM2="$SIM2_JSON"
SIM2_ID="$(python - <<'PY'
import json, os
print(json.loads(os.environ["SIM2"])["simulation_id"])
PY
)"
echo "Simulation id: $SIM2_ID"

echo "==> Calculate"
curl -sS -X POST "$BASE/api/simulations/$SIM2_ID/calcul/" \
  -H "$AUTH2" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> Details"
curl -sS "$BASE/api/simulations/$SIM2_ID/" -H "$AUTH2" | python -m json.tool

echo "==> OK CAS 2 (compte: $EMAIL2 / $PASS)"

echo ""
echo "======================================================"
echo " CAS 3 — ETUDIANT montant max (50k, 96 mois, Toulouse)"
echo "======================================================"

EMAIL3="etu_cas3_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> Register: $EMAIL3"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL3\",\"password\":\"$PASS\",\"nom\":\"Bernard\",\"prenom\":\"Luc\"}" \
  | python -m json.tool

echo "==> JWT token"
TOKENS3="$(curl -sS -X POST "$BASE/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL3\",\"password\":\"$PASS\"}")"
export TOKENS3
ACCESS3="$(python - <<'PY'
import json, os
print(json.loads(os.environ["TOKENS3"])["access"])
PY
)"
AUTH3="Authorization: Bearer $ACCESS3"

echo "==> Create simulation ETUDIANT (25 ans, Toulouse, 50k, 96 mois)"
SIM3_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH3" \
  -d '{
    "type_credit":"ETUDIANT",
    "profil_financier":{
      "age":25,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Toulouse",
      "revenus_mensuels":"900.00","autres_revenus":"300.00",
      "charges_logement":"500.00","charges_credits":"0.00","autres_charges":"100.00",
      "type_contrat":"ETUDIANT","anciennete_emploi_mois":0
    },
    "projet_credit":{
      "type_credit":"ETUDIANT","montant_souhaite":"50000.00",
      "duree_mois":96,"apport_personnel":"0.00"
    }
  }')"
export SIM3="$SIM3_JSON"
SIM3_ID="$(python - <<'PY'
import json, os
print(json.loads(os.environ["SIM3"])["simulation_id"])
PY
)"
echo "Simulation id: $SIM3_ID"

echo "==> Calculate"
curl -sS -X POST "$BASE/api/simulations/$SIM3_ID/calcul/" \
  -H "$AUTH3" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> Details"
curl -sS "$BASE/api/simulations/$SIM3_ID/" -H "$AUTH3" | python -m json.tool

echo "==> OK CAS 3 (compte: $EMAIL3 / $PASS)"

echo ""
echo "======================================================"
echo " CAS 4 — ETUDIANT anonyme (18 ans, Rennes, 8k, 24 mois)"
echo "======================================================"

echo "==> Create simulation ETUDIANT anonyme (18 ans, sans revenus)"
SIM4_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" \
  -d '{
    "type_credit":"ETUDIANT",
    "profil_financier":{
      "age":18,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Rennes",
      "revenus_mensuels":"0.00","autres_revenus":"500.00",
      "charges_logement":"250.00","charges_credits":"0.00","autres_charges":"0.00",
      "type_contrat":"ETUDIANT","anciennete_emploi_mois":0
    },
    "projet_credit":{
      "type_credit":"ETUDIANT","montant_souhaite":"8000.00",
      "duree_mois":24,"apport_personnel":"0.00"
    }
  }')"
export SIM4="$SIM4_JSON"
SIM4_ID="$(python - <<'PY'
import json, os
print(json.loads(os.environ["SIM4"])["simulation_id"])
PY
)"
echo "Simulation anonyme id: $SIM4_ID"

echo "==> Calculate"
curl -sS -X POST "$BASE/api/simulations/$SIM4_ID/calcul/" \
  -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> Details"
curl -sS "$BASE/api/simulations/$SIM4_ID/" | python -m json.tool

echo "==> OK CAS 4 (anonyme)"

echo ""
echo "======================================================"
echo " OK — tous les cas ETUDIANT terminés"
echo "======================================================"
