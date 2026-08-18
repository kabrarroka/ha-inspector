#!/usr/bin/env bash
set -euo pipefail

HA_HOST="homeassistant"
REMOTE_COMPONENT="/config/custom_components/ha_inspector"
LOCAL_COMPONENT="$(pwd)/custom_components/ha_inspector"
BACKUP_BASE="$HOME/ha-inspector-backups"

echo "==> Verificando componente local..."
test -d "$LOCAL_COMPONENT"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOCAL_BACKUP="${BACKUP_BASE}/ha_inspector-${TIMESTAMP}"

echo "==> Creando copia de seguridad local..."
mkdir -p "$LOCAL_BACKUP"

rsync -a \
    "$HA_HOST:$REMOTE_COMPONENT/" \
    "$LOCAL_BACKUP/"

echo "Backup: $LOCAL_BACKUP"

echo "==> Sincronizando HA Inspector..."
rsync -av --delete \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    "$LOCAL_COMPONENT/" \
    "$HA_HOST:$REMOTE_COMPONENT/"

echo "==> Versión desplegada:"
ssh "$HA_HOST" "
    grep -E '\"version\"|VERSION' \
    '$REMOTE_COMPONENT/manifest.json' \
    '$REMOTE_COMPONENT/const.py' 2>/dev/null || true
"

echo "==> Despliegue completado."
