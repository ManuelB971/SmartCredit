#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8001}"
EMAIL="${1:-}"
PASS="${2:-}"

if [[ -z "$EMAIL" || -z "$PASS" ]]; then
  echo "Usage: $0 <email> <password>"
  echo "Ex:    $0 lea@example.com motdepassefort"
  exit 1
fi

echo "==> 1) JWT token"
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
echo "Token OK"

echo ""
echo "==> 2) GET /api/auth/me/ — profil courant (avec token)"
curl -sS "$BASE/api/auth/me/" -H "$AUTH" | python -m json.tool

echo ""
echo "==> 3) GET /api/auth/me/ SANS token — doit retourner 401"
curl -sS "$BASE/api/auth/me/" | python -m json.tool

echo ""
echo "==> OK test_auth_me terminé"
