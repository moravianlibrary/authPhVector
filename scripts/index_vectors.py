"""
Indexovací skript — parsuje MARCXML soubory autorit, generuje embeddingy
a nahrává je do Pinecone.

Použití:
  # Zpracuje všechny aut_*.xml v nadřazeném adresáři:
  python index_vectors.py

  # Konkrétní soubory:
  python index_vectors.py aut_ph.xml aut_ge.xml

  # Explicitní pole (přepíše auto-detekci):
  python index_vectors.py aut_ph.xml --preferred-field 150 --variant-field 450

Mapování polí (auto-detekce podle názvu souboru):
  aut_ph.xml  →  150 / 450  (předmětová hesla)
  aut_ge.xml  →  151 / 451  (geografická jména)

Vyžaduje:
  export PINECONE_API_KEY=pcsk_...
  export PINECONE_INDEX_HOST=https://authph-xxxx.svc.aped-xxxx.pinecone.io
  pip install -r requirements.txt
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from lxml import etree
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

NS = "http://www.loc.gov/MARC21/slim"
DATA_DIR = Path(__file__).parent.parent
MODEL_NAME = "intfloat/multilingual-e5-small"
INDEX_NAME = "authph"
RECORDS_PER_BATCH = 200
ENCODE_BATCH_SIZE = 64
E5_PASSAGE = "passage: "

# Auto-detekce polí podle části názvu souboru
FIELD_MAP: dict[str, tuple[str, str]] = {
    "ph": ("150", "450"),
    "ge": ("151", "451"),
}


def detect_fields(path: Path) -> tuple[str, str]:
    stem = path.stem  # např. "aut_ph"
    for key, fields in FIELD_MAP.items():
        if f"_{key}" in stem or stem.endswith(key):
            return fields
    sys.exit(
        f"Nelze auto-detekovat pole pro '{path.name}'. "
        f"Zadejte --preferred-field a --variant-field ručně."
    )


def parse_records(xml_path: Path, preferred_field: str, variant_field: str):
    """
    Stream-parsuje MARCXML. Vrací generátor slovníků.
    lxml iterparse + elem.clear() udržuje konstantní paměť.
    """
    record_tag = f"{{{NS}}}record"
    for _event, elem in etree.iterparse(str(xml_path), events=["end"], tag=record_tag):
        rec_id = elem.findtext(f"{{{NS}}}controlfield[@tag='001']") or ""
        preferred = None
        variants = []

        mdt = []
        konspekt = []
        authority_url = ""
        for df in elem.findall(f"{{{NS}}}datafield"):
            tag = df.get("tag")
            if tag == preferred_field:
                val = df.findtext(f"{{{NS}}}subfield[@code='a']")
                if val:
                    preferred = val.strip()
            elif tag == variant_field:
                val = df.findtext(f"{{{NS}}}subfield[@code='a']")
                if val:
                    variants.append(val.strip())
            elif tag == "080":
                val = df.findtext(f"{{{NS}}}subfield[@code='a']")
                if val:
                    mdt.append(val.strip())
            elif tag == "072":
                a = df.findtext(f"{{{NS}}}subfield[@code='a']") or ""
                x = df.findtext(f"{{{NS}}}subfield[@code='x']") or ""
                if a:
                    entry = f"{a.strip()} - {x.strip()}" if x else a.strip()
                    konspekt.append(entry)
            elif tag == "998":
                val = df.findtext(f"{{{NS}}}subfield[@code='a']")
                if val:
                    authority_url = val.strip()

        elem.clear()

        if preferred:
            yield {"record_id": rec_id, "preferred": preferred, "variants": variants, "mdt": mdt, "konspekt": konspekt, "authority_url": authority_url}


def records_to_vectors(
    records: list[dict], model: SentenceTransformer, source: str
) -> list[dict]:
    """
    Převede dávku záznamů na vektory pro Pinecone upsert.
    `source` se uloží do metadat (např. "ph", "ge").
    """
    ids, texts, metas = [], [], []

    for rec in records:
        ids.append(f"{rec['record_id']}_pref")
        texts.append(E5_PASSAGE + rec["preferred"])
        metas.append({
            "term": rec["preferred"],
            "preferred": rec["preferred"],
            "is_variant": False,
            "record_id": rec["record_id"],
            "source": source,
            "mdt": "|".join(rec["mdt"]),
            "konspekt": "|".join(rec["konspekt"]),
            "authority_url": rec["authority_url"],
        })

        for i, variant in enumerate(rec["variants"]):
            ids.append(f"{rec['record_id']}_var_{i}")
            texts.append(E5_PASSAGE + variant)
            metas.append({
                "term": variant,
                "preferred": rec["preferred"],
                "is_variant": True,
                "record_id": rec["record_id"],
                "source": source,
                "mdt": "|".join(rec["mdt"]),
                "konspekt": "|".join(rec["konspekt"]),
                "authority_url": rec["authority_url"],
            })

    embeddings = model.encode(
        texts,
        batch_size=ENCODE_BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return [
        {"id": id_, "values": emb.tolist(), "metadata": meta}
        for id_, emb, meta in zip(ids, embeddings, metas)
    ]


def ensure_index(pc: Pinecone) -> None:
    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        logging.info(f"Vytvářím Pinecone index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logging.info("Index vytvořen.")
    else:
        logging.info(f"Index '{INDEX_NAME}' již existuje.")


def index_file(
    xml_path: Path,
    preferred_field: str,
    variant_field: str,
    model: SentenceTransformer,
    index,
) -> int:
    source = xml_path.stem.split("_")[-1]  # "aut_ph" → "ph"
    batch: list[dict] = []
    total_vectors = 0

    for record in tqdm(
        parse_records(xml_path, preferred_field, variant_field),
        desc=xml_path.name,
        unit="rec",
    ):
        batch.append(record)
        if len(batch) >= RECORDS_PER_BATCH:
            vectors = records_to_vectors(batch, model, source)
            index.upsert(vectors=vectors)
            total_vectors += len(vectors)
            batch = []

    if batch:
        vectors = records_to_vectors(batch, model, source)
        index.upsert(vectors=vectors)
        total_vectors += len(vectors)

    return total_vectors


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexuje MARCXML autority do Pinecone.")
    parser.add_argument(
        "files",
        nargs="*",
        help="Cesty k XML souborům. Bez argumentu: všechny aut_*.xml v kořeni projektu.",
    )
    parser.add_argument(
        "--preferred-field",
        help="Číslo pole preferovaného hesla (přepíše auto-detekci).",
    )
    parser.add_argument(
        "--variant-field",
        help="Číslo pole variantního hesla (přepíše auto-detekci).",
    )
    args = parser.parse_args()

    api_key = os.environ.get("PINECONE_API_KEY")
    index_host = os.environ.get("PINECONE_INDEX_HOST")

    if not api_key:
        sys.exit("Chybí PINECONE_API_KEY")

    # Sestavit seznam souborů
    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = sorted(DATA_DIR.glob("aut_*.xml"))
        if not paths:
            sys.exit(f"Nenalezeny žádné soubory aut_*.xml v {DATA_DIR}")

    for p in paths:
        if not p.exists():
            sys.exit(f"Soubor nenalezen: {p}")

    # Pokud jsou explicitní pole, platí pro všechny soubory
    explicit_fields = None
    if args.preferred_field or args.variant_field:
        if not (args.preferred_field and args.variant_field):
            sys.exit("Zadejte obě volby: --preferred-field i --variant-field")
        explicit_fields = (args.preferred_field, args.variant_field)

    logging.info(f"Soubory ke zpracování: {[p.name for p in paths]}")

    pc = Pinecone(api_key=api_key)
    ensure_index(pc)
    index = pc.Index(host=index_host) if index_host else pc.Index(INDEX_NAME)

    model = SentenceTransformer(MODEL_NAME)
    logging.info(f"Model '{MODEL_NAME}' načten.")

    grand_total = 0
    for xml_path in paths:
        pf, vf = explicit_fields if explicit_fields else detect_fields(xml_path)
        logging.info(f"{xml_path.name}: pole {pf}/{vf}")
        count = index_file(xml_path, pf, vf, model, index)
        logging.info(f"{xml_path.name}: nahráno {count} vektorů")
        grand_total += count

    logging.info(f"Hotovo. Celkem nahráno vektorů: {grand_total}")


if __name__ == "__main__":
    main()
