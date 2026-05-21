#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/../scripts"
ENV_FILE="$SCRIPT_DIR/../.env.local"

if [[ -f "$ENV_FILE" ]]; then
  set -o allexport
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +o allexport
  echo "Načteny proměnné z .env.local"
fi

: "${PINECONE_API_KEY:?Chybí PINECONE_API_KEY v .env.local nebo prostředí}"

bash "$SCRIPT_DIR/setup_venv.sh"

echo "Running indexing script..."
exec "$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/index_vectors.py" "$@"
