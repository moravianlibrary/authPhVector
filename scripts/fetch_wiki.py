"""
Extrahuje Wikipedia stránky z lokálního multistream dumpu cs.wikipedia.org.
Výstup: data/wiki/{record_id}.txt (čistý text bez wiki markup)

Použití:
  python fetch_wiki.py                         # všechny aut_*.xml v data/aut/
  python fetch_wiki.py data/aut/aut_ph.xml data/aut/aut_ge.xml   # konkrétní soubory
  python fetch_wiki.py --force                 # přepsat existující soubory
  python fetch_wiki.py --dump-dir /jiný/adresář

Vyžaduje:
  pip install -r requirements.txt
  data/wiki_dump/cswiki-latest-pages-articles-multistream-index.txt.bz2
  data/wiki_dump/cswiki-latest-pages-articles-multistream.xml.bz2
"""

import argparse
import bz2
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

import mwparserfromhell
from lxml import etree
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

NS = "http://www.loc.gov/MARC21/slim"
DATA_DIR = Path(__file__).parent.parent
AUT_DIR = DATA_DIR / "data" / "aut"
WIKI_DIR = DATA_DIR / "data" / "wiki"
INDEX_FILENAME = "cswiki-latest-pages-articles-multistream-index.txt.bz2"
DUMP_FILENAME = "cswiki-latest-pages-articles-multistream.xml.bz2"
REDIRECT_FILENAME = "redirect.txt"
READ_BUFFER = 2_000_000  # 2 MB — větší než max chunk (~1.46 MB)


# ---------------------------------------------------------------------------
# Index a přesměrování
# ---------------------------------------------------------------------------

def load_index(index_path: Path) -> tuple[dict[str, int], dict[str, str]]:
    """
    Načte bz2 index soubor. Vrací:
      title_to_offset: {title → byte_offset v dump souboru}
      pageid_to_title: {page_id → title}
    """
    title_to_offset: dict[str, int] = {}
    pageid_to_title: dict[str, str] = {}
    logging.info(f"Načítám index: {index_path.name} ...")
    with bz2.open(index_path, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split(":", 2)
            if len(parts) != 3:
                continue
            offset_s, pid, title = parts
            title_to_offset[title] = int(offset_s)
            pageid_to_title[pid] = title
    logging.info(f"Index načten: {len(title_to_offset):,} titulů")
    return title_to_offset, pageid_to_title


def _decode_hex_escapes(s: str) -> str:
    """Dekóduje \\xNN MySQL hex escape sekvence jako UTF-8 bajty."""
    def repl(m: re.Match) -> str:
        hex_str = m.group(0).replace("\\x", "")
        return bytes.fromhex(hex_str).decode("utf-8", errors="replace")
    return re.sub(r"(?:\\x[0-9a-fA-F]{2})+", repl, s)


def load_redirects(
    redirect_path: Path, pageid_to_title: dict[str, str]
) -> dict[str, str]:
    """
    Načte redirect.txt (formát: page_id\\tns\\t'target_title').
    Vrací {source_title → target_title}.
    """
    title_to_target: dict[str, str] = {}
    logging.info(f"Načítám přesměrování: {redirect_path.name} ...")
    with open(redirect_path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            pid, _ns, raw = parts[0], parts[1], parts[2].strip("'")
            target = _decode_hex_escapes(raw).replace("_", " ")
            src = pageid_to_title.get(pid)
            if src and target:
                title_to_target[src] = target
    logging.info(f"Přesměrování načtena: {len(title_to_target):,}")
    return title_to_target


# ---------------------------------------------------------------------------
# URL → název článku
# ---------------------------------------------------------------------------

def url_to_title(url: str) -> str:
    """
    'https://cs.wikipedia.org/wiki/Karibsk%C3%A1_krize' → 'Karibská krize'
    """
    path = url.split("/wiki/", 1)[-1]
    return unquote(path).replace("_", " ")


def resolve_title(
    raw_title: str,
    title_to_offset: dict[str, int],
    title_to_target: dict[str, str],
) -> tuple[str, int] | None:
    """
    Najde kanonický titul a byte offset v dump souboru.
    Zkouší: přesný titul, titul s velkým prvním písmenem, následuje 1 redirect hop.
    Vrací (titul, offset) nebo None.
    """
    candidates = [raw_title]
    if raw_title and raw_title[0].islower():
        candidates.append(raw_title[0].upper() + raw_title[1:])

    for candidate in candidates:
        offset = title_to_offset.get(candidate)
        if offset is None:
            continue
        # Sledovat přesměrování (max 1 hop)
        target = title_to_target.get(candidate)
        if target:
            target_offset = title_to_offset.get(target)
            if target_offset is not None:
                return target, target_offset
            # Cíl přesměrování není v indexu
            return None
        return candidate, offset

    return None


# ---------------------------------------------------------------------------
# Čtení a parsování multistream dump chunku
# ---------------------------------------------------------------------------

def read_chunk(dump_file, offset: int) -> bytes:
    """
    Přeskočí na offset, dekomprimuje přesně jeden bz2 stream.
    BZ2Decompressor se zastaví po konci streamu (EOF marker).
    """
    dump_file.seek(offset)
    raw = dump_file.read(READ_BUFFER)
    return bz2.BZ2Decompressor().decompress(raw)


def parse_chunk(xml_bytes: bytes) -> etree._Element:
    """
    Fragment XML (sekvence <page>...</page> bez root elementu) obalí
    do <mediawiki> a zparsuje pomocí lxml.
    """
    return etree.fromstring(b"<mediawiki>" + xml_bytes + b"</mediawiki>")


def extract_page_text(root: etree._Element, title: str) -> str | None:
    """Najde stránku podle titulu a vrátí její wikitext."""
    for page in root.findall("page"):
        if page.findtext("title") == title:
            text_el = page.find(".//text")
            return text_el.text or "" if text_el is not None else ""
    return None


# ---------------------------------------------------------------------------
# Wikitext → čistý text
# ---------------------------------------------------------------------------

_REDIRECT_RE = re.compile(r"^#(?:REDIRECT|PŘESMĚRUJ)\b", re.IGNORECASE)


def strip_wikitext(wikitext: str) -> str | None:
    """
    Odstraní veškerý wiki markup pomocí mwparserfromhell.
    Vrací None pokud je stránka přesměrování nebo výsledek prázdný.
    """
    if _REDIRECT_RE.match(wikitext):
        return None
    plain = mwparserfromhell.parse(wikitext).strip_code()
    plain = re.sub(r"\n{3,}", "\n\n", plain).strip()
    return plain or None


# ---------------------------------------------------------------------------
# Iterace MARCXML záznamů (zachováno z původního skriptu)
# ---------------------------------------------------------------------------

def iter_wiki_records(xml_path: Path):
    """Vrací (rec_id, url) pro záznamy s cs.wikipedia.org odkazem v poli 856$u."""
    record_tag = f"{{{NS}}}record"
    for _, elem in etree.iterparse(str(xml_path), events=["end"], tag=record_tag):
        rec_id = elem.findtext(f"{{{NS}}}controlfield[@tag='001']") or ""
        for df in elem.findall(f"{{{NS}}}datafield[@tag='856']"):
            url = df.findtext(f"{{{NS}}}subfield[@code='u']") or ""
            if "cs.wikipedia.org" in url.lower():
                yield rec_id, url.strip()
                break
        elem.clear()


# ---------------------------------------------------------------------------
# Hlavní zpracování
# ---------------------------------------------------------------------------

def process(
    xml_paths: list[Path],
    dump_dir: Path,
    force: bool,
) -> tuple[int, int, int]:
    """
    Průchod 1: Shromáždí (rec_id, canonical_title, offset) pro všechny záznamy.
    Průchod 2: Seskupí podle offsetu → každý chunk decomprimuje jen jednou.
    Vrací (staženo, přeskočeno, chyb).
    """
    index_path = dump_dir / INDEX_FILENAME
    dump_path = dump_dir / DUMP_FILENAME
    redirect_path = dump_dir / REDIRECT_FILENAME

    for p in (index_path, dump_path):
        if not p.exists():
            sys.exit(f"Soubor nenalezen: {p}")

    title_to_offset, pageid_to_title = load_index(index_path)

    if redirect_path.exists():
        title_to_target = load_redirects(redirect_path, pageid_to_title)
    else:
        logging.warning("redirect.txt nenalezen — přesměrování nebudou sledována")
        title_to_target = {}

    # Průchod 1: sestavit pracovní seznam
    work: list[tuple[str, str, int]] = []  # (rec_id, canonical_title, offset)
    skipped = 0
    not_found = 0

    for xml_path in xml_paths:
        logging.info(f"Prohledávám {xml_path.name} ...")
        for rec_id, url in iter_wiki_records(xml_path):
            out_path = WIKI_DIR / f"{rec_id}.txt"
            if out_path.exists() and not force:
                skipped += 1
                continue
            raw_title = url_to_title(url)
            result = resolve_title(raw_title, title_to_offset, title_to_target)
            if result is None:
                logging.debug(f"{rec_id}: titul nenalezen v indexu: {raw_title!r}")
                not_found += 1
                continue
            canonical_title, offset = result
            work.append((rec_id, canonical_title, offset))

    logging.info(
        f"K zpracování: {len(work)}, přeskočeno: {skipped}, nenalezeno: {not_found}"
    )

    if not work:
        return 0, skipped, not_found

    # Průchod 2: seskupit podle offsetu → minimální počet dekompresí
    offset_groups: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for rec_id, title, offset in work:
        offset_groups[offset].append((rec_id, title))

    downloaded = errors = 0
    WIKI_DIR.mkdir(parents=True, exist_ok=True)

    with open(dump_path, "rb") as dump_file:
        for offset, items in tqdm(offset_groups.items(), desc="chunky", unit="chunk"):
            try:
                xml_bytes = read_chunk(dump_file, offset)
                root = parse_chunk(xml_bytes)
            except Exception as exc:
                logging.error(f"Chunk offset={offset}: chyba dekomprese/parsování — {exc}")
                errors += len(items)
                continue

            for rec_id, title in items:
                try:
                    wikitext = extract_page_text(root, title)
                    if wikitext is None:
                        logging.warning(f"{rec_id}: stránka {title!r} nenalezena v chunku")
                        errors += 1
                        continue
                    plain = strip_wikitext(wikitext)
                    if plain is None:
                        logging.warning(f"{rec_id}: {title!r} je přesměrování nebo prázdná")
                        errors += 1
                        continue
                    (WIKI_DIR / f"{rec_id}.txt").write_text(plain, encoding="utf-8")
                    downloaded += 1
                except Exception as exc:
                    logging.error(f"{rec_id}: {title!r} — {exc}")
                    errors += 1

    return downloaded, skipped, errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrahuje Wikipedia stránky z lokálního multistream dumpu."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Cesty k MARCXML souborům. Bez argumentu: všechny aut_*.xml v data/aut/.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Přepsat existující soubory.",
    )
    parser.add_argument(
        "--dump-dir",
        type=Path,
        default=DATA_DIR / "data" / "wiki_dump",
        help="Adresář s Wikipedia dump soubory (výchozí: data/wiki_dump/).",
    )
    args = parser.parse_args()

    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = sorted(AUT_DIR.glob("aut_*.xml"))
        if not paths:
            sys.exit(f"Nenalezeny žádné soubory aut_*.xml v {AUT_DIR}")

    for p in paths:
        if not p.exists():
            sys.exit(f"Soubor nenalezen: {p}")

    downloaded, skipped, errors = process(paths, args.dump_dir, args.force)
    logging.info(
        f"Hotovo. Zapsáno: {downloaded}, přeskočeno: {skipped}, chyb/nenalezeno: {errors}"
    )


if __name__ == "__main__":
    main()
