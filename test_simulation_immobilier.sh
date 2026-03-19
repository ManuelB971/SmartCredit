#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"
PASS="${PASS:-motdepassefort}"

echo "==> 0) Migrations + seed"
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py seed_offres || true

echo ""
echo "======================================================"
echo " CAS 1 — IMMOBILIER CDI célibataire standard"
echo "======================================================"

EMAIL="immo_cas1_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> Register: $EMAIL"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"nom\":\"Dupont\",\"prenom\":\"Lea\"}" \
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

echo "==> Create simulation IMMOBILIER (CDI, 32 ans, Paris, 250k, 240 mois)"
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

echo "==> Calculate"
curl -sS -X POST "$BASE/api/simulations/$SIM_ID/calcul/" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> Details (PRUDENT / EQUILIBRE / CONFORT)"
curl -sS "$BASE/api/simulations/$SIM_ID/" -H "$AUTH" | python -m json.tool

echo "==> OK CAS 1 (compte: $EMAIL / $PASS)"

echo ""
echo "======================================================"
echo " CAS 2 — IMMOBILIER MARIE 2 enfants (Lyon, 350k, 300 mois)"
echo "======================================================"

EMAIL2="immo_cas2_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> Register: $EMAIL2"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL2\",\"password\":\"$PASS\",\"nom\":\"Martin\",\"prenom\":\"Paul\"}" \
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

echo "==> Create simulation IMMOBILIER (MARIE, 2 enfants, 5200 revenus)"
SIM2_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH2" \
  -d '{
    "type_credit":"IMMOBILIER",
    "profil_financier":{
      "age":38,"situation_familiale":"MARIE","nombre_enfants":2,"ville":"Lyon",
      "revenus_mensuels":"5200.00","autres_revenus":"400.00",
      "charges_logement":"900.00","charges_credits":"300.00","autres_charges":"200.00",
      "type_contrat":"CDI","anciennete_emploi_mois":84
    },
    "projet_credit":{
      "type_credit":"IMMOBILIER","montant_souhaite":"350000.00",
      "duree_mois":300,"apport_personnel":"50000.00"
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
echo " CAS 3 — IMMOBILIER durée courte (120 mois, Bordeaux)"
echo "======================================================"

EMAIL3="immo_cas3_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> Register: $EMAIL3"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL3\",\"password\":\"$PASS\",\"nom\":\"Durand\",\"prenom\":\"Claire\"}" \
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

echo "==> Create simulation IMMOBILIER (45 ans, PACSE, 180k, 120 mois)"
SIM3_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH3" \
  -d '{
    "type_credit":"IMMOBILIER",
    "profil_financier":{
      "age":45,"situation_familiale":"PACSE","nombre_enfants":1,"ville":"Bordeaux",
      "revenus_mensuels":"6000.00","autres_revenus":"500.00",
      "charges_logement":"1000.00","charges_credits":"0.00","autres_charges":"100.00",
      "type_contrat":"CDI","anciennete_emploi_mois":120
    },
    "projet_credit":{
      "type_credit":"IMMOBILIER","montant_souhaite":"180000.00",
      "duree_mois":120,"apport_personnel":"40000.00"
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
echo " CAS 4 — IMMOBILIER anonyme sans compte"
echo "======================================================"

echo "==> Create simulation IMMOBILIER anonyme (CDD, Nantes, 200k)"
SIM4_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" \
  -d '{
    "type_credit":"IMMOBILIER",
    "profil_financier":{
      "age":29,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Nantes",
      "revenus_mensuels":"2900.00","autres_revenus":"0.00",
      "charges_logement":"600.00","charges_credits":"0.00","autres_charges":"50.00",
      "type_contrat":"CDD","anciennete_emploi_mois":12
    },
    "projet_credit":{
      "type_credit":"IMMOBILIER","montant_souhaite":"200000.00",
      "duree_mois":240,"apport_personnel":"10000.00"
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
echo " OK — tous les cas IMMOBILIER terminés"
echo "======================================================"
