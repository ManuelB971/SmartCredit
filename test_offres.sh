#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"

echo "==> 0) Seed offres bancaires"
docker compose exec backend python manage.py seed_offres || true

echo ""
echo "==> 1) GET /api/offres/ — toutes les offres"
curl -sS "$BASE/api/offres/" | python -m json.tool

echo ""
echo "==> 2) GET /api/offres/?type_credit=IMMOBILIER"
curl -sS "$BASE/api/offres/?type_credit=IMMOBILIER" | python -m json.tool

echo ""
echo "==> 3) GET /api/offres/?type_credit=ETUDIANT"
curl -sS "$BASE/api/offres/?type_credit=ETUDIANT" | python -m json.tool

echo ""
echo "==> 4) GET /api/offres/?type_credit=INVALIDE (filtre ignore, retourne tout)"
curl -sS "$BASE/api/offres/?type_credit=INVALIDE" | python -m json.tool

echo ""
echo "==> OK test_offres terminé"
