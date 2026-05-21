# ADR 001 — Next.js jako framework

**Status:** Accepted  
**Datum:** 2026-05-18

## Context

Aplikace potřebuje:
1. React UI pro vyhledávací formulář a zobrazení výsledků
2. Serverový endpoint pro volání HuggingFace a Pinecone API (API klíče nesmí být odhaleny v prohlížeči)
3. Nasazení na Vercel bez vlastní serverové infrastruktury

Alternativy: samostatný Express/FastAPI backend + Vite/CRA frontend; SvelteKit; Remix.

## Decision

Zvolíme Next.js App Router s Vercel nasazením.

Next.js poskytuje API routes přímo v rámci projektu — není nutné spravovat samostatný backend ani CORS. Vercel nativně rozumí Next.js a nasazení probíhá bez konfigurace. Pro proof-of-concept projekt s jedním vývojářem je nulová infrastrukturní zátěž rozhodující.

## Consequences

**Pozitivní:**
- Jeden projekt, jeden deployment, jeden příkaz `npm run dev`
- Serverové API routes v TypeScriptu sdílejí typy s frontendem (`export interface SearchResult`)
- Vercel preview deployments zdarma pro každý push

**Negativní:**
- Vendor lock-in na Vercel/Next.js ekosystém
- Python indexovací skripty musí zůstat samostatné (mimo Next.js)
