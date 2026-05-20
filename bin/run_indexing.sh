#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/../scripts"

bash "$SCRIPT_DIR/setup_venv.sh"

echo "Running indexing script..."
exec "$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/index_vectors.py" "$@"
