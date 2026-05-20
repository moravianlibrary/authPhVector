#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Downloading data"
AUT_URL_BASE="https://aleph.nkp.cz/data"
AUT_FILES=(aut_ph.xml.gz aut_ge.xml.gz aut_sk.xml.gz)
AUT_DIR="$SCRIPT_DIR/../data/aut"
mkdir -p "$AUT_DIR"
for filename in "${AUT_FILES[@]}"; do
    echo "  Downloading: $filename"
    wget -q --show-progress "$AUT_URL_BASE/$filename" -O - | gunzip > "$AUT_DIR/${filename%.gz}"
done

echo "Downloading Wikipedia dump files..."
DUMP_DIR="$SCRIPT_DIR/../data/wiki_dump"
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
