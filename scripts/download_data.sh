#!/usr/bin/env bash

echo "Downloading data"
wget "https://aleph.nkp.cz/data/aut_ph.xml.gz" -O aut_ph.xml.gz
gunzip aut_ph.xml.gz
wget "https://aleph.nkp.cz/data/aut_ge.xml.gz" -O aut_ge.xml.gz
gunzip aut_ge.xml.gz


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Downloading Wikipedia dump files..."
DUMP_DIR="$SCRIPT_DIR/../wiki_dump"
mkdir -p "$DUMP_DIR"
while IFS= read -r url; do
    [ -z "$url" ] && continue
    filename=$(basename "$url")
    dest="$DUMP_DIR/$filename"
    if [ -f "$dest" ]; then
        echo "  Already exists: $filename"
    else
        echo "  Downloading: $filename"
        wget -q --show-progress "$url" -O "$dest"
    fi
done < "$DUMP_DIR/urls2.txt"

echo "Fetching Wikipedia pages..."
VENV="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
fi
"$VENV/bin/python" "$SCRIPT_DIR/fetch_wiki.py"

echo "Done"
