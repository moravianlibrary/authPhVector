#!/usr/bin/env bash

echo "Downloading data"
wget "https://aleph.nkp.cz/data/aut_ph.xml.gz" -O aut_ph.xml.gz
gunzip aut_ph.xml.gz
wget "https://aleph.nkp.cz/data/aut_ge.xml.gz" -O aut_ge.xml.gz
gunzip aut_ge.xml.gz


echo "Fetching Wikipedia pages..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet requests beautifulsoup4 lxml tqdm
fi
"$VENV/bin/python" "$SCRIPT_DIR/fetch_wiki.py"

echo "Done"
