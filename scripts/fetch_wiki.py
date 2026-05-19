"""
Stáhne Wikipedia stránky odkazované z MARCXML záznamů (pole 856$u).
Text z div.mw-content-text se uloží do data/wiki/{record_id}.txt.

Použití:
  python fetch_wiki.py                   # všechny aut_*.xml v kořeni projektu
  python fetch_wiki.py aut_ph.xml        # konkrétní soubor(y)
  python fetch_wiki.py --force           # přepsat existující soubory
  python fetch_wiki.py --delay 1.0       # prodleva mezi požadavky (výchozí: 0.5 s)
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from lxml import etree
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

NS = "http://www.loc.gov/MARC21/slim"
DATA_DIR = Path(__file__).parent.parent
WIKI_DIR = DATA_DIR / "data" / "wiki"

USER_AGENT = "authphvector/1.0 (https://github.com/authphvector; bot)"
TIMEOUT = 15
MAX_RETRIES = 3


def iter_wiki_records(xml_path: Path):
    """Vrací (rec_id, url) pro záznamy s Wikipedia odkazem v poli 856$u."""
    record_tag = f"{{{NS}}}record"
    for _, elem in etree.iterparse(str(xml_path), events=["end"], tag=record_tag):
        rec_id = elem.findtext(f"{{{NS}}}controlfield[@tag='001']") or ""
        for df in elem.findall(f"{{{NS}}}datafield[@tag='856']"):
            url = df.findtext(f"{{{NS}}}subfield[@code='u']") or ""
            if "wikipedia" in url.lower():
                yield rec_id, url.strip()
                break  # jeden záznam → první Wikipedia URL
        elem.clear()


def fetch_text(url: str, session: requests.Session) -> str | None:
    """
    Stáhne stránku a vrátí čistý text z div.mw-content-text.
    Při HTTP 429 čeká a zkusí znovu (max MAX_RETRIES pokusů).
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 60))
                logging.warning(f"Rate limit (429), čekám {wait} s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                raise
            logging.warning(f"Pokus {attempt}/{MAX_RETRIES} selhal ({exc}), zkouším znovu...")
            time.sleep(2 ** attempt)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "sup", "table"]):
            tag.decompose()

        content = soup.find("div", class_="mw-content-text")
        if not content:
            return None

        return content.get_text(separator="\n", strip=True)

    return None


def process_file(
    xml_path: Path,
    session: requests.Session,
    force: bool,
    delay: float,
) -> tuple[int, int, int]:
    """Zpracuje jeden XML soubor. Vrací (staženo, přeskočeno, chyb)."""
    downloaded = skipped = errors = 0

    records = list(iter_wiki_records(xml_path))
    logging.info(f"{xml_path.name}: nalezeno {len(records)} Wikipedia odkazů")

    for rec_id, url in tqdm(records, desc=xml_path.name, unit="rec"):
        out_path = WIKI_DIR / f"{rec_id}.txt"

        if out_path.exists() and not force:
            skipped += 1
            continue

        try:
            text = fetch_text(url, session)
            if text:
                out_path.write_text(text, encoding="utf-8")
                downloaded += 1
            else:
                logging.warning(f"{rec_id}: div.mw-content-text nenalezen ({url})")
                errors += 1
        except Exception as exc:
            logging.error(f"{rec_id}: chyba při stahování {url} — {exc}")
            errors += 1

        time.sleep(delay)

    return downloaded, skipped, errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stáhne Wikipedia stránky z MARCXML záznamů."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Cesty k XML souborům. Bez argumentu: všechny aut_*.xml v kořeni projektu.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Přepsat existující soubory.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Prodleva mezi HTTP požadavky v sekundách (výchozí: 0.5).",
    )
    args = parser.parse_args()

    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = sorted(DATA_DIR.glob("aut_*.xml"))
        if not paths:
            sys.exit(f"Nenalezeny žádné soubory aut_*.xml v {DATA_DIR}")

    for p in paths:
        if not p.exists():
            sys.exit(f"Soubor nenalezen: {p}")

    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Výstupní adresář: {WIKI_DIR}")

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    total_dl = total_skip = total_err = 0
    for xml_path in paths:
        dl, skip, err = process_file(xml_path, session, args.force, args.delay)
        total_dl += dl
        total_skip += skip
        total_err += err
        logging.info(
            f"{xml_path.name}: staženo={dl}, přeskočeno={skip}, chyb={err}"
        )

    logging.info(
        f"Celkem: staženo={total_dl}, přeskočeno={total_skip}, chyb={total_err}"
    )


if __name__ == "__main__":
    main()
