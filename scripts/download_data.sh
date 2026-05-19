#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Downloading data"
wget "https://aleph.nkp.cz/data/aut_ph.xml.gz" -O aut_ph.xml.gz
gunzip aut_ph.xml.gz
wget "https://aleph.nkp.cz/data/aut_ge.xml.gz" -O aut_ge.xml.gz
gunzip aut_ge.xml.gz

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

bash "$SCRIPT_DIR/setup_venv.sh"

echo "Fetching Wikipedia pages..."
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/fetch_wiki.py"

echo "Done"
