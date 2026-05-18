"""
Jednorázový indexovací skript.
Parsuje aut_ph.xml, generuje embeddingy a nahrává je do Pinecone.

Použití:
  export PINECONE_API_KEY=pcsk_...
  export PINECONE_INDEX_HOST=https://authph-xxxx.svc.aped-xxxx.pinecone.io
  python index_vectors.py

Vyžaduje:
  pip install -r requirements.txt
"""

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
XML_PATH = Path(__file__).parent.parent / "aut_ph.xml"
MODEL_NAME = "intfloat/multilingual-e5-small"
INDEX_NAME = "authph"
RECORDS_PER_BATCH = 200   # ~400–800 vektorů na Pinecone upsert volání
ENCODE_BATCH_SIZE = 64
E5_PASSAGE = "passage: "


def parse_records(xml_path: Path):
    """
    Stream-parsuje MARCXML, vrací generátor slovníků.
    lxml iterparse + elem.clear() udržuje konstantní paměť (O(1 záznam)).
    """
    record_tag = f"{{{NS}}}record"
    for _event, elem in etree.iterparse(str(xml_path), events=["end"], tag=record_tag):
        rec_id = elem.findtext(f"{{{NS}}}controlfield[@tag='001']") or ""
        preferred = None
        variants = []

        for df in elem.findall(f"{{{NS}}}datafield"):
            tag = df.get("tag")
            if tag == "150":
                val = df.findtext(f"{{{NS}}}subfield[@code='a']")
                if val:
                    preferred = val.strip()
            elif tag == "450":
                val = df.findtext(f"{{{NS}}}subfield[@code='a']")
                if val:
                    variants.append(val.strip())

        elem.clear()

        if preferred:
            yield {"record_id": rec_id, "preferred": preferred, "variants": variants}


def records_to_vectors(records: list[dict], model: SentenceTransformer) -> list[dict]:
    """
    Převede dávku záznamů na vektory pro Pinecone upsert.
    Každý term (preferred + variants) je samostatný vektor s metadaty.
    e5 modely vyžadují prefix "passage: " pro indexované dokumenty.
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
        })

        for i, variant in enumerate(rec["variants"]):
            ids.append(f"{rec['record_id']}_var_{i}")
            texts.append(E5_PASSAGE + variant)
            metas.append({
                "term": variant,
                "preferred": rec["preferred"],
                "is_variant": True,
                "record_id": rec["record_id"],
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


def main():
    api_key = os.environ.get("PINECONE_API_KEY")
    index_host = os.environ.get("PINECONE_INDEX_HOST")

    if not api_key:
        sys.exit("Chybí PINECONE_API_KEY")

    if not XML_PATH.exists():
        sys.exit(f"Soubor nenalezen: {XML_PATH}")

    pc = Pinecone(api_key=api_key)
    ensure_index(pc)

    if index_host:
        index = pc.Index(host=index_host)
    else:
        index = pc.Index(INDEX_NAME)

    model = SentenceTransformer(MODEL_NAME)
    logging.info(f"Model '{MODEL_NAME}' načten.")

    batch: list[dict] = []
    total_vectors = 0

    logging.info(f"Parsování {XML_PATH} a indexování...")

    for record in tqdm(parse_records(XML_PATH), desc="Záznamy", unit="rec"):
        batch.append(record)
        if len(batch) >= RECORDS_PER_BATCH:
            vectors = records_to_vectors(batch, model)
            index.upsert(vectors=vectors)
            total_vectors += len(vectors)
            batch = []

    if batch:
        vectors = records_to_vectors(batch, model)
        index.upsert(vectors=vectors)
        total_vectors += len(vectors)

    logging.info(f"Hotovo. Celkem nahráno vektorů: {total_vectors}")
    logging.info("Ověřte počet v Pinecone console nebo přes: index.describe_index_stats()")


if __name__ == "__main__":
    main()
