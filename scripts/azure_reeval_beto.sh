#!/usr/bin/env bash
# Dispara la re-evaluación de Pack C en Azure con el modelo BETO refinado
# (4 categorías: depresion, ansiedad, adaptativo, neutral).
#
# Uso:
#   AZURE_URL="https://<tu-app>.azurewebsites.net" ./scripts/azure_reeval_beto.sh
#
# La re-eval toma ~10 min (BETO CPU sobre 26 aplicaciones × 20 frases).
set -euo pipefail

: "${AZURE_URL:?Falta AZURE_URL. Ej: AZURE_URL=https://sami-app-9921877.azurewebsites.net}"
: "${ADMIN_EMAIL:=admin@admin.com}"
: "${ADMIN_PASSWORD:=Admin12345}"

echo "→ Login admin en ${AZURE_URL}"
TOKEN=$(curl -sS -X POST "${AZURE_URL}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

if [[ -z "${TOKEN}" ]]; then
    echo "✗ No se obtuvo token — verificá credenciales o URL"
    exit 1
fi

echo "→ Disparando re-eval Pack C (esto tarda ~10 min, no cierres)"
curl -X POST "${AZURE_URL}/api/v1/admin/piloto/re-evaluar-beto" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"filtro_plantilla_nombre":"%Pack C%"}' \
    --max-time 900

echo ""
echo "✓ Listo. Verificá el dashboard clínico en ${AZURE_URL}."
