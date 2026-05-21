#!/usr/bin/env bash
set -euo pipefail

command -v python3 >/dev/null || { echo "Chyba: python3 není nainstalován" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/../scripts"
VENV="$SCRIPTS_DIR/.venv"

if [ ! -d "$VENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

echo "Installing/updating dependencies..."
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r "$SCRIPTS_DIR/requirements.txt"

echo "Dependencies ready."
