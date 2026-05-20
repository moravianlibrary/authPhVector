"""
Indexovací skript — parsuje MARCXML soubory autorit, generuje embeddingy
a nahrává je do Pinecone.

Použití:
  # Zpracuje všechny aut_*.xml v data/aut/:
  python index_vectors.py

  # Konkrétní soubory:
  python index_vectors.py data/aut/aut_ph.xml data/aut/aut_ge.xml

  # Explicitní pole (přepíše auto-detekci):
  python index_vectors.py data/aut/aut_ph.xml --preferred-field 150 --variant-field 450

Mapování polí (auto-detekce podle názvu souboru):
  aut_ph.xml  →  150 / 450  (předmětová hesla)
  aut_ge.xml  →  151 / 451  (geografická jména)
  aut_sk.xml  →  190 / 490  (konspekt; preferred = "a - x", vector = x)

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
MODEL_CONFIGS: dict[str, dict] = {
    "intfloat/multilingual-e5-small": {
        "index_name": "authph",
        "index_host_env": "PINECONE_INDEX_HOST",
        "dimension": 384,
        "passage_prefix": "passage: ",
    },
    "intfloat/multilingual-e5-large": {
        "index_name": "autph-large",
        "index_host_env": "PINECONE_INDEX_HOST_LARGE",
        "dimension": 1024,
        "passage_prefix": "passage: ",
    },
}
DEFAULT_MODEL = "intfloat/multilingual-e5-small"
RECORDS_PER_BATCH = 200
ENCODE_BATCH_SIZE = 64
AUT_DIR = DATA_DIR / "data" / "aut"
WIKI_DIR = DATA_DIR / "data" / "wiki"
WIKI_MAX_CHARS = 1000

# Auto-detekce polí podle části názvu souboru
FIELD_MAP: dict[str, tuple[str, str]] = {
    "ph": ("150", "450"),
    "ge": ("151", "451"),
    "sk": ("190", "490"),
    "fd": ("155", "455"),
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


def parse_records(xml_path: Path, preferred_field: str, variant_field: str, combine_subfields: bool = False):
    """
    Stream-parsuje MARCXML. Vrací generátor slovníků.
    lxml iterparse + elem.clear() udržuje konstantní paměť.
    combine_subfields=True: preferred = "$a - $x", vector_text = "$x" (pro sk/190).
    """
    record_tag = f"{{{NS}}}record"
    for _event, elem in etree.iterparse(str(xml_path), events=["end"], tag=record_tag):
        rec_id = elem.findtext(f"{{{NS}}}controlfield[@tag='001']") or ""
        wiki_path = WIKI_DIR / f"{rec_id}.txt"
        wiki_text = wiki_path.read_text(encoding="utf-8")[:WIKI_MAX_CHARS] if wiki_path.exists() else ""
        preferred = None
        vector_text = ""
        variants = []

        mdt = []
        konspekt = []
        authority_url = ""
        for df in elem.findall(f"{{{NS}}}datafield"):
            tag = df.get("tag")
            if tag == preferred_field:
                a_val = (df.findtext(f"{{{NS}}}subfield[@code='a']") or "").strip()
                x_val = (df.findtext(f"{{{NS}}}subfield[@code='x']") or "").strip()
                if combine_subfields and a_val and x_val:
                    preferred = f"{a_val} - {x_val}"
                    vector_text = x_val
                elif a_val or x_val:
                    preferred = a_val or x_val
                    vector_text = preferred
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
            yield {"record_id": rec_id, "preferred": preferred, "vector_text": vector_text, "variants": variants, "mdt": mdt, "konspekt": konspekt, "authority_url": authority_url, "wiki_text": wiki_text}


def build_text(term: str, wiki: str, passage_prefix: str) -> str:
    return f"{passage_prefix}{term}\n\n{wiki}" if wiki else f"{passage_prefix}{term}"


def records_to_vectors(
    records: list[dict], model: SentenceTransformer, source: str, passage_prefix: str
) -> list[dict]:
    """
    Převede dávku záznamů na vektory pro Pinecone upsert.
    `source` se uloží do metadat (např. "ph", "ge").
    """
    ids, texts, metas = [], [], []

    for rec in records:
        ids.append(f"{rec['record_id']}_pref")
        texts.append(build_text(rec["vector_text"], rec["wiki_text"], passage_prefix))
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
            texts.append(build_text(variant, rec["wiki_text"], passage_prefix))
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


def ensure_index(pc: Pinecone, index_name: str, dimension: int) -> None:
    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        logging.info(f"Vytvářím Pinecone index '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logging.info("Index vytvořen.")
    else:
        logging.info(f"Index '{index_name}' již existuje.")


def index_file(
    xml_path: Path,
    preferred_field: str,
    variant_field: str,
    model: SentenceTransformer,
    index,
    passage_prefix: str,
) -> int:
    source = xml_path.stem.split("_")[-1]  # "aut_ph" → "ph"
    combine = source == "sk"
    batch: list[dict] = []
    total_vectors = 0

    for record in tqdm(
        parse_records(xml_path, preferred_field, variant_field, combine_subfields=combine),
        desc=xml_path.name,
        unit="rec",
    ):
        batch.append(record)
        if len(batch) >= RECORDS_PER_BATCH:
            vectors = records_to_vectors(batch, model, source, passage_prefix)
            index.upsert(vectors=vectors)
            total_vectors += len(vectors)
            batch = []

    if batch:
        vectors = records_to_vectors(batch, model, source, passage_prefix)
        index.upsert(vectors=vectors)
        total_vectors += len(vectors)

    return total_vectors


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexuje MARCXML autority do Pinecone.")
    parser.add_argument(
        "files",
        nargs="*",
        help="Cesty k XML souborům. Bez argumentu: všechny aut_*.xml v data/aut/.",
    )
    parser.add_argument(
        "--preferred-field",
        help="Číslo pole preferovaného hesla (přepíše auto-detekci).",
    )
    parser.add_argument(
        "--variant-field",
        help="Číslo pole variantního hesla (přepíše auto-detekci).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        choices=list(MODEL_CONFIGS),
        help=f"Embedding model (výchozí: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Zařízení pro výpočet embeddingů (např. cuda, cpu). Výchozí: cuda pokud dostupné, jinak cpu.",
    )
    args = parser.parse_args()

    model_cfg = MODEL_CONFIGS[args.model]
    index_name = model_cfg["index_name"]
    dimension = model_cfg["dimension"]
    passage_prefix = model_cfg["passage_prefix"]

    api_key = os.environ.get("PINECONE_API_KEY")
    index_host = os.environ.get(model_cfg["index_host_env"])

    if not api_key:
        sys.exit("Chybí PINECONE_API_KEY")

    # Sestavit seznam souborů
    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = sorted(AUT_DIR.glob("aut_*.xml"))
        if not paths:
            sys.exit(f"Nenalezeny žádné soubory aut_*.xml v {AUT_DIR}")

    for p in paths:
        if not p.exists():
            sys.exit(f"Soubor nenalezen: {p}")

    # Pokud jsou explicitní pole, platí pro všechny soubory
    explicit_fields = None
    if args.preferred_field or args.variant_field:
        if not (args.preferred_field and args.variant_field):
            sys.exit("Zadejte obě volby: --preferred-field i --variant-field")
        explicit_fields = (args.preferred_field, args.variant_field)

    logging.info(f"Model: {args.model}, index: {index_name}, dim: {dimension}")
    logging.info(f"Soubory ke zpracování: {[p.name for p in paths]}")

    pc = Pinecone(api_key=api_key)
    ensure_index(pc, index_name, dimension)
    index = pc.Index(host=index_host) if index_host else pc.Index(index_name)

    import torch
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = SentenceTransformer(args.model, device=device)
    logging.info(f"Model '{args.model}' načten na zařízení: {device}.")

    grand_total = 0
    for xml_path in paths:
        pf, vf = explicit_fields if explicit_fields else detect_fields(xml_path)
        logging.info(f"{xml_path.name}: pole {pf}/{vf}")
        count = index_file(xml_path, pf, vf, model, index, passage_prefix)
        logging.info(f"{xml_path.name}: nahráno {count} vektorů")
        grand_total += count

    logging.info(f"Hotovo. Celkem nahráno vektorů: {grand_total}")


if __name__ == "__main__":
    main()
