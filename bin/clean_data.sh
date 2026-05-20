#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"

echo "Cleaning downloaded data..."
rm -rf "$DATA_DIR/aut"
rm -rf "$DATA_DIR/wiki_dump"
rm -rf "$DATA_DIR/wiki"
echo "Done."
