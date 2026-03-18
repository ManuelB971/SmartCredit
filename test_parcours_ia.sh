#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"
EMAIL="${1:-}"
PASS="${2:-}"
NOM="${3:-Test}"
PRENOM="${4:-User}"

if [[ -z "$EMAIL" || -z "$PASS" ]]; then
  echo "Usage: $0 <email> <password> [nom] [prenom]"
  echo "Ex:    $0 lea@example.com motdepassefort Dupont Lea"
  exit 1
fi

echo "==> 0) Pré-check Ollama (local)"
if ! curl -sS "http://localhost:11434/api/tags" >/dev/null 2>&1; then
  echo "Ollama ne répond pas sur localhost:11434."
  echo "1) Installe Ollama"
  echo "2) Lance Ollama"
  echo "3) Puis: ollama pull llama3.1:8b"
  exit 1
fi
echo "Ollama OK"

echo "==> 1) Migrations + seed (pas de restart Docker)"
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py seed_offres || true

echo "==> 2) Register (ignore si déjà existant)"
curl -sS -X POST "$BASE/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"nom\":\"$NOM\",\"prenom\":\"$PRENOM\"}" \
  >/dev/null || true

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
echo "Access token OK"

echo "==> 4) Create simulation"
SIM_JSON="$(curl -sS -X POST "$BASE/api/simulations/" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "type_credit":"IMMOBILIER",
    "profil_financier":{
      "age":32,
      "situation_familiale":"CELIBATAIRE",
      "nombre_enfants":0,
      "ville":"Paris",
      "revenus_mensuels":"3500.00",
      "autres_revenus":"0.00",
      "charges_logement":"750.00",
      "charges_credits":"150.00",
      "autres_charges":"0.00",
      "type_contrat":"CDI",
      "anciennete_emploi_mois":36
    },
    "projet_credit":{
      "type_credit":"IMMOBILIER",
      "montant_souhaite":"250000.00",
      "duree_mois":240,
      "apport_personnel":"30000.00"
    }
  }')"
export SIM="$SIM_JSON"
SIM_ID="$(python3 - <<'PY'
import json, os
print(json.loads(os.environ["SIM"])["simulation_id"])
PY
)"
echo "Simulation id: $SIM_ID"

echo "==> 5) Calculate (avec IA si dispo)"
CALC_JSON="$(curl -sS -X POST "$BASE/api/simulations/$SIM_ID/calcul/" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{}')"
export CALC="$CALC_JSON"
echo "$CALC_JSON" | python3 -m json.tool

echo "==> 6) Vérif IA (status + score + erreur)"
python3 - <<'PY'
import json, os
obj = json.loads(os.environ["CALC"])
ai = obj.get("ai") or {}
print("ai.status =", ai.get("status"))
print("ai.score  =", ai.get("score"))
if ai.get("error"):
    print("ai.error  =", ai.get("error"))
PY

echo "==> 7) Détails simulation (inclut explication IA)"
curl -sS "$BASE/api/simulations/$SIM_ID/" -H "$AUTH" | python3 -m json.tool

echo "==> OK"

