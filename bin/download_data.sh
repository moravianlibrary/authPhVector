#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/../scripts"

echo "Downloading data"
AUT_URL_BASE="https://aleph.nkp.cz/data"
AUT_FILES=(aut_ph.xml.gz aut_ge.xml.gz aut_sk.xml.gz aut_fd.xml.gz)
AUT_DIR="$SCRIPT_DIR/../data/aut"
mkdir -p "$AUT_DIR"
for filename in "${AUT_FILES[@]}"; do
    echo "  Downloading: $filename"
    wget -q --show-progress "$AUT_URL_BASE/$filename" -O - | gunzip > "$AUT_DIR/${filename%.gz}"
done

echo "Downloading Wikipedia dump files..."
DUMP_DIR="$SCRIPT_DIR/../data/wiki_dump"
mkdir -p "$DUMP_DIR"
WIKI_FILES=(
    "https://dumps.wikimedia.org/cswiki/latest/cswiki-latest-pages-articles-multistream-index.txt.bz2"
    "https://dumps.wikimedia.org/cswiki/latest/cswiki-latest-pages-articles-multistream.xml.bz2"
)
for url in "${WIKI_FILES[@]}"; do
    filename=$(basename "$url")
    dest="$DUMP_DIR/$filename"
    if [ -f "$dest" ]; then
        echo "  Already exists: $filename"
    else
        echo "  Downloading: $filename"
        wget -q --show-progress "$url" -O "$dest"
    fi
done

bash "$SCRIPT_DIR/setup_venv.sh"

echo "Downloading Wikipedia redirects..."
REDIRECT_OUT="$DUMP_DIR/redirect.txt"
if [ ! -f "$REDIRECT_OUT" ]; then
    wget -q --show-progress \
        "https://dumps.wikimedia.org/cswiki/latest/cswiki-latest-redirect.sql.gz" \
        -O - | gunzip | "$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/parse_redirect_sql.py" \
        > "$REDIRECT_OUT"
else
    echo "  Already exists: redirect.txt"
fi

echo "Fetching Wikipedia pages..."
"$SCRIPTS_DIR/.venv/bin/python" "$SCRIPTS_DIR/fetch_wiki.py"

echo "Done"
