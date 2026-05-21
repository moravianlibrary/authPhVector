# ADR 004 — Každý embedding model má vlastní Pinecone index

**Status:** Accepted  
**Datum:** 2026-05-20

## Context

Po přidání druhého embedding modelu (E5-large) bylo nutné rozhodnout, jak organizovat Pinecone indexy. Možnosti:
1. Jeden sdílený index s metadatovým polem `model_id`
2. Každý model má vlastní index

## Decision

Každý embedding model dostane vlastní Pinecone index s dimenzí odpovídající danému modelu.

Embedding vektory různých modelů jsou geometricky nekompatibilní — cosine similarity mezi vektorem z E5-small a vektorem z BGE-M3 je nesmyslná. Sdílený index by vyhledávání na dotaz z jiného modelu, než který záznam indexoval, dával špatné výsledky. Navíc E5-small generuje 384-dim vektory a E5-large/BGE-M3 1024-dim — Pinecone index má pevně danou dimenzi.

Konfigurace indexu (název, host URL) je centralizována v `config/models.json`, takže přidání nového modelu nevyžaduje změny v kódu — jen záznam v JSON a nový Pinecone index.

## Consequences

**Pozitivní:**
- Korektní výsledky vyhledávání bez míchání vektorových prostorů
- Jasná izolace dat per model

**Negativní:**
- Indexace musí proběhnout zvlášť pro každý model
- Pinecone free tier má limit na počet indexů
- Více host URL proměnných prostředí (`PINECONE_INDEX_HOST`, `PINECONE_INDEX_HOST_LARGE`, `PINECONE_INDEX_HOST_BGE_M3`)
