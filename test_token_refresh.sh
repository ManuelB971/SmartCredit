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

echo "==> 1) JWT token (obtain)"
TOKENS="$(curl -sS -X POST "$BASE/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")"
echo "$TOKENS" | python -m json.tool
export TOKENS
REFRESH="$(python - <<'PY'
import json, os
print(json.loads(os.environ["TOKENS"])["refresh"])
PY
)"
echo "Refresh token OK"

echo ""
echo "==> 2) POST /api/auth/token/refresh/ — nouveau access token"
REFRESH_RESP="$(curl -sS -X POST "$BASE/api/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}")"
echo "$REFRESH_RESP" | python -m json.tool

echo ""
echo "==> 3) Utiliser le nouveau token sur /api/auth/me/"
export REFRESH_RESP
NEW_ACCESS="$(python - <<'PY'
import json, os
print(json.loads(os.environ["REFRESH_RESP"])["access"])
PY
)"
curl -sS "$BASE/api/auth/me/" -H "Authorization: Bearer $NEW_ACCESS" | python -m json.tool

echo ""
echo "==> 4) Token refresh invalide — doit retourner 401"
curl -sS -X POST "$BASE/api/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"tokeninvalide"}' | python -m json.tool

echo ""
echo "==> OK test_token_refresh terminé"
