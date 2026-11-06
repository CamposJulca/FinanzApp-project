#!/usr/bin/env bash
# =============================================================================
# Despliegue de FinanzApp: build del frontend → collectstatic → reinicio.
#
# Por qué existe: el 2026-11-06 se recompiló frontend/dist pero no se corrió
# collectstatic ni se reinició gunicorn. WhiteNoise indexa los estáticos al
# arrancar, así que index.html apuntaba a index-<hash>.js/.css que devolvían
# 404 y la app cargaba en blanco. Este script hace los tres pasos siempre, en
# orden, y al final comprueba que los assets que referencia index.html sirvan.
#
# Uso (producción, desde la raíz del repo):
#   infra/deploy.sh
#
# Variables opcionales (para staging o pruebas):
#   PROJECT_DIR   raíz del repo              (por defecto: la de este script)
#   ENV_FILE      archivo de entorno         (por defecto: $PROJECT_DIR/.env)
#   VENV_DIR      virtualenv de Django       (por defecto: $PROJECT_DIR/backend/.venv)
#   SERVICE       unidad systemd a reiniciar (por defecto: finanzapp)
#   RESTART_CMD   comando de reinicio; si se define, reemplaza a systemctl
#   BASE_URL      URL para la verificación   (por defecto: http://127.0.0.1:8090)
#   SKIP_NPM_CI=1 no reinstala node_modules (usa los existentes)
#
# Rollback: no hay migraciones aquí. Para volver atrás basta con hacer checkout
# del commit anterior y volver a ejecutar este script.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env}"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/backend/.venv}"
SERVICE="${SERVICE:-finanzapp}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8090}"

log()  { printf '\n==> %s\n' "$*"; }
fail() { printf '\n[ERROR] %s\n' "$*" >&2; exit 1; }

[[ -d "$PROJECT_DIR/frontend" ]] || fail "No existe $PROJECT_DIR/frontend"
[[ -f "$ENV_FILE" ]]             || fail "No existe el archivo de entorno $ENV_FILE"
[[ -x "$VENV_DIR/bin/python" ]]  || fail "No existe el virtualenv $VENV_DIR"

cd "$PROJECT_DIR"
log "Proyecto: $PROJECT_DIR  (rama: $(git branch --show-current 2>/dev/null || echo '?'), commit: $(git rev-parse --short HEAD 2>/dev/null || echo '?'))"

if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  echo "[AVISO] Hay cambios sin commitear; se desplegará el árbol de trabajo tal cual."
fi

# --- 1. Build del frontend ---------------------------------------------------
log "1/3 Build del frontend"
cd "$PROJECT_DIR/frontend"
if [[ "${SKIP_NPM_CI:-0}" != "1" ]]; then
  npm ci --no-audit --no-fund
fi
npm run build
[[ -f dist/index.html ]] || fail "El build no generó frontend/dist/index.html"

# --- 2. collectstatic --------------------------------------------------------
log "2/3 collectstatic"
cd "$PROJECT_DIR/backend"
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a
"$VENV_DIR/bin/python" manage.py collectstatic --noinput

# --- 3. Reinicio -------------------------------------------------------------
# WhiteNoise sólo descubre los archivos nuevos al arrancar el proceso.
log "3/3 Reinicio"
if [[ -n "${RESTART_CMD:-}" ]]; then
  bash -c "$RESTART_CMD"
else
  sudo systemctl restart "$SERVICE"
  systemctl is-active --quiet "$SERVICE" || fail "El servicio $SERVICE no quedó activo"
fi

# --- Verificación ------------------------------------------------------------
log "Verificación de assets contra $BASE_URL"
assets=$(grep -oE '/assets/[^"]+\.(js|css)' "$PROJECT_DIR/frontend/dist/index.html" | sort -u)
[[ -n "$assets" ]] || fail "index.html no referencia assets; build inesperado"

ok=0
for i in $(seq 1 20); do
  if curl -fsS -o /dev/null "$BASE_URL/login/"; then ok=1; break; fi
  sleep 1
done
[[ "$ok" == "1" ]] || fail "La app no responde en $BASE_URL tras el reinicio"

errores=0
for asset in $assets; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL$asset")
  printf '  %s  %s\n' "$code" "$asset"
  [[ "$code" == "200" ]] || errores=$((errores + 1))
done
[[ "$errores" == "0" ]] || fail "$errores asset(s) no responden 200: la app cargaría en blanco"

log "Despliegue OK"
