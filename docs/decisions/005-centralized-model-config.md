# ADR 005 — Centralizovaná konfigurace modelů v config/models.json

**Status:** Accepted  
**Datum:** 2026-05-21

## Context

Konfigurace embedding modelů (ID modelu, Pinecone index, dimenze, prefixy) byla původně duplikována: v `src/app/api/search/route.ts` jako TypeScript objekt a v `scripts/index_vectors.py` jako Python dict. Přidání třetího modelu (BGE-M3) ukázalo, že toto duplikování je nepraktické — změna ve dvou souborech s rizikem nekonzistence.

## Decision

Vytvoříme `config/models.json` jako jediný zdroj pravdy. Next.js importuje JSON nativně (`import modelsConfig from "../../../../config/models.json"`), Python čte JSON přes stdlib `json.load()`. Oba sdílí přesně stejná data bez přepisování.

Soubor obsahuje i `_docs` sekci s inline dokumentací každého pole — JSON schema bez závislostí na externích nástrojích.

## Consequences

**Pozitivní:**
- Přidání nového modelu = jeden soubor, nulové riziko nekonzistence
- UI dropdown se generuje automaticky z `models.json`
- Python skript a TypeScript API route jsou vždy v sync

**Negativní:**
- JSON neumožňuje komentáře (řešeno přes `_docs` klíč)
- Při chybě v JSON souboru selžou obě aplikace najednou
