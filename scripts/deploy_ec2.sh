#!/usr/bin/env bash
set -Eeuo pipefail

PACKAGE_PATH="${1:-dist/todo-app.tar.gz}"
: "${EC2_HOST:?Define EC2_HOST como variable protegida de GitLab}"
: "${SSH_PRIVATE_KEY:?Define SSH_PRIVATE_KEY como variable protegida de tipo File}"
: "${SSH_KNOWN_HOSTS:?Define SSH_KNOWN_HOSTS como variable protegida de tipo File}"

EC2_USER="${EC2_USER:-ec2-user}"
APP_DIR="${APP_DIR:-/home/ec2-user/todo-app}"
SERVICE_NAME="todo-app.service"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
DEPLOY_ID="${CI_PIPELINE_ID:-$(date +%s)}"
REMOTE_ARCHIVE="/tmp/todo-app-${DEPLOY_ID}.tar.gz"

if [[ ! -f "$PACKAGE_PATH" ]]; then
  echo "No existe el artefacto: $PACKAGE_PATH" >&2
  exit 1
fi

chmod 600 "$SSH_PRIVATE_KEY"
chmod 600 "$SSH_KNOWN_HOSTS"
export GITLAB_SSH_KEY="$SSH_PRIVATE_KEY"
export GITLAB_KNOWN_HOSTS="$SSH_KNOWN_HOSTS"

ssh_cmd=(ssh -i "$GITLAB_SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$GITLAB_KNOWN_HOSTS")
scp_cmd=(scp -i "$GITLAB_SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$GITLAB_KNOWN_HOSTS")
REMOTE="${EC2_USER}@${EC2_HOST}"

echo "Transfiriendo artefacto a ${REMOTE}:${REMOTE_ARCHIVE}"
"${scp_cmd[@]}" "$PACKAGE_PATH" "${REMOTE}:${REMOTE_ARCHIVE}"

"${ssh_cmd[@]}" "$REMOTE" bash -s -- "$REMOTE_ARCHIVE" "$APP_DIR" "$SERVICE_NAME" "$HEALTH_URL" <<'REMOTE_SCRIPT'
set -Eeuo pipefail
archive="$1"
app_dir="$2"
service="$3"
health_url="$4"
stage_dir="$(mktemp -d /tmp/todo-app-release.XXXXXX)"
cleanup() {
  rm -rf -- "$stage_dir"
  rm -f -- "$archive"
}
trap cleanup EXIT

mkdir -p "$app_dir"
tar -tzf "$archive" | while IFS= read -r entry; do
  case "$entry" in
    *.db|*.db/*|*/tareas.db|*/tareas.db/*)
      echo "El artefacto contiene un archivo SQLite prohibido: $entry" >&2
      exit 1
      ;;
  esac
done
tar -xzf "$archive" -C "$stage_dir"

# Copiar solo el contenido del artefacto. No hay borrado ni sincronización
# destructiva; como el paquete excluye *.db, la base existente se conserva.
cp -a "$stage_dir"/. "$app_dir"/

if [[ ! -x "$app_dir/venv/bin/python" ]]; then
  python3.12 -m venv "$app_dir/venv"
fi
"$app_dir/venv/bin/python" -m pip install --upgrade pip
"$app_dir/venv/bin/python" -m pip install -r "$app_dir/requirements.txt"

sudo systemctl restart "$service"
sudo systemctl is-active --quiet "$service"

healthy=0
for attempt in {1..12}; do
  if curl --fail --silent --show-error "$health_url"; then
    echo
    healthy=1
    break
  fi
  echo "Health check no disponible (intento $attempt/12); esperando 5 segundos..."
  sleep 5
done

if [[ "$healthy" -ne 1 ]]; then
  echo "El endpoint de salud no respondió correctamente: $health_url" >&2
  sudo systemctl --no-pager --full status "$service" || true
  exit 1
fi
REMOTE_SCRIPT

echo "Despliegue completado y health check correcto."
