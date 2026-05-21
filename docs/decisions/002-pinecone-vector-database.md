# ADR 002 — Pinecone jako vektorová databáze

**Status:** Accepted  
**Datum:** 2026-05-18

## Context

Sémantické vyhledávání vyžaduje vektorovou databázi schopnou ANN (approximate nearest neighbor) vyhledávání přes stovky tisíc vektorů. Potřebujeme:
- Filtrování výsledků podle metadat (typ záznamu `source`)
- Škálování bez vlastní serverové správy
- Přijatelná latence (~100–300 ms) pro interaktivní UI

Alternativy: Weaviate, Qdrant (self-hosted), pgvector (PostgreSQL), Chroma (lokální).

## Decision

Zvolíme Pinecone serverless.

Pro proof-of-concept projekt je spravovaná služba bez nutnosti provozovat vlastní server klíčová. Pinecone serverless tier nevyžaduje předplacení ani platbu za idle — platí se pouze za uložené vektory a dotazy. Metadata filtering (`source: { $eq: "ph" }`) je nativně podporován bez schématu.

Nevýhodou je cold start serverless indexu (první dotaz po delší nečinnosti může trvat 1–2 s), ale pro tuto aplikaci je to přijatelné.

## Consequences

**Pozitivní:**
- Nulová infrastrukturní správa
- Škáluje automaticky
- Metadata filtering bez konfigurace

**Negativní:**
- Vendor lock-in
- Indexovaná data jsou mimo vlastní infrastrukturu
- Každý embedding model vyžaduje vlastní index (viz [ADR 004](004-separate-index-per-model.md))
