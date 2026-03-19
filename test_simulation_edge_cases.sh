#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"
PASS="${PASS:-motdepassefort}"

echo "==> 0) Migrations + seed"
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py seed_offres || true

EMAIL="edge_$(date +%Y%m%d_%H%M%S)_$RANDOM@example.com"

echo "==> Register + token"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"nom\":\"Edge\",\"prenom\":\"Case\"}" \
  | python -m json.tool

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
echo "======================================================"
echo " CAS 1 — Simulation inexistante → doit retourner 404"
echo "======================================================"

echo "==> GET /api/simulations/999999/ (inexistante)"
curl -sS -X GET "$BASE/api/simulations/999999/" -H "$AUTH" | python -m json.tool

echo "==> POST /api/simulations/999999/calcul/ (inexistante)"
curl -sS -X POST "$BASE/api/simulations/999999/calcul/" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> OK CAS 1"

echo ""
echo "======================================================"
echo " CAS 2 — Apport = Montant → capital 0 → doit retourner 400"
echo "======================================================"

echo "==> Create simulation (apport = montant = 200k)"
SIM2_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{
    "type_credit":"IMMOBILIER",
    "profil_financier":{
      "age":35,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Paris",
      "revenus_mensuels":"4000.00","autres_revenus":"0.00",
      "charges_logement":"800.00","charges_credits":"0.00","autres_charges":"0.00",
      "type_contrat":"CDI","anciennete_emploi_mois":24
    },
    "projet_credit":{
      "type_credit":"IMMOBILIER","montant_souhaite":"200000.00",
      "duree_mois":240,"apport_personnel":"200000.00"
    }
  }')"
export SIM2="$SIM2_JSON"
SIM2_ID="$(python - <<'PY'
import json, os
print(json.loads(os.environ["SIM2"])["simulation_id"])
PY
)"
echo "Simulation id: $SIM2_ID"

echo "==> Calculate (doit retourner 400)"
curl -sS -X POST "$BASE/api/simulations/$SIM2_ID/calcul/" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> OK CAS 2"

echo ""
echo "======================================================"
echo " CAS 3 — Taux endettement > 35% (revenus faibles, gros montant)"
echo "======================================================"

echo "==> Create simulation (2000 revenus, 300k, endettement eleve)"
SIM3_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{
    "type_credit":"IMMOBILIER",
    "profil_financier":{
      "age":30,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Paris",
      "revenus_mensuels":"2000.00","autres_revenus":"0.00",
      "charges_logement":"500.00","charges_credits":"200.00","autres_charges":"100.00",
      "type_contrat":"CDI","anciennete_emploi_mois":12
    },
    "projet_credit":{
      "type_credit":"IMMOBILIER","montant_souhaite":"300000.00",
      "duree_mois":240,"apport_personnel":"0.00"
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
  -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> Details (verifier taux_endettement et score_faisabilite)"
curl -sS "$BASE/api/simulations/$SIM3_ID/" -H "$AUTH" | python -m json.tool

echo "==> OK CAS 3"

echo ""
echo "======================================================"
echo " CAS 4 — Payload incomplet → doit retourner 400"
echo "======================================================"

echo "==> Create simulation sans profil_financier ni projet_credit"
curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{"type_credit":"IMMOBILIER"}' | python -m json.tool

echo "==> OK CAS 4"

echo ""
echo "======================================================"
echo " CAS 5 — type_credit invalide → doit retourner 400"
echo "======================================================"

echo "==> Create simulation avec type_credit VOITURE (invalide)"
curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{
    "type_credit":"VOITURE",
    "profil_financier":{
      "age":30,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Paris",
      "revenus_mensuels":"3000.00","autres_revenus":"0.00",
      "charges_logement":"700.00","charges_credits":"0.00","autres_charges":"0.00",
      "type_contrat":"CDI","anciennete_emploi_mois":24
    },
    "projet_credit":{
      "type_credit":"VOITURE","montant_souhaite":"15000.00",
      "duree_mois":60,"apport_personnel":"0.00"
    }
  }' | python -m json.tool

echo "==> OK CAS 5"

echo ""
echo "======================================================"
echo " CAS 6 — Double calcul sur meme simulation (idempotent)"
echo "======================================================"

echo "==> Create simulation ETUDIANT"
SIM6_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{
    "type_credit":"ETUDIANT",
    "profil_financier":{
      "age":22,"situation_familiale":"CELIBATAIRE","nombre_enfants":0,"ville":"Paris",
      "revenus_mensuels":"600.00","autres_revenus":"0.00",
      "charges_logement":"300.00","charges_credits":"0.00","autres_charges":"50.00",
      "type_contrat":"ETUDIANT","anciennete_emploi_mois":0
    },
    "projet_credit":{
      "type_credit":"ETUDIANT","montant_souhaite":"15000.00",
      "duree_mois":48,"apport_personnel":"0.00"
    }
  }')"
export SIM6="$SIM6_JSON"
SIM6_ID="$(python - <<'PY'
import json, os
print(json.loads(os.environ["SIM6"])["simulation_id"])
PY
)"
echo "Simulation id: $SIM6_ID"

echo "==> Premier calcul"
curl -sS -X POST "$BASE/api/simulations/$SIM6_ID/calcul/" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> Deuxieme calcul (doit fonctionner pareil)"
curl -sS -X POST "$BASE/api/simulations/$SIM6_ID/calcul/" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python -m json.tool

echo "==> OK CAS 6"

echo ""
echo "======================================================"
echo " OK — tous les cas limites terminés (compte: $EMAIL / $PASS)"
echo "======================================================"
