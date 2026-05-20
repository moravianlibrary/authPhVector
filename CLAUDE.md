# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Semantic search over Czech National Authority File (Národní autority ČR) records. Users type a query; the app generates a vector embedding via HuggingFace and finds similar terms in Pinecone.

## Commands

```bash
npm run dev        # Start development server (localhost:3000)
npm run build      # Production build
npm run lint       # ESLint via Next.js
```

No test suite exists yet.

### Python indexing script (one-time data ingestion)

```bash
pip install -r scripts/requirements.txt
python scripts/index_vectors.py   # parses aut_ph.xml → uploads vectors to Pinecone
```

If there is error PEP 688, you can install dependencies and run indexing with this command:

```
bin/run_indexing.sh
```

`aut_ph.xml` is gitignored (large MARCXML file, ~100 MB).

## Architecture

```
User query
  → page.tsx (debounced 400 ms, retries on 503)
  → POST /api/search  (src/app/api/search/route.ts)
      → HuggingFace Inference API  (multilingual-e5-small, 384-dim, "query: " prefix)
      → Pinecone serverless query  (topK * 3 to allow dedup)
      → dedup by preferredTerm, return top N
  → SearchResult[] displayed with colour-coded scores
```

### Key files
- `src/app/page.tsx` — single-page UI, search state, retry logic
- `src/app/api/search/route.ts` — embedding + vector search, dedup
- `scripts/index_vectors.py` — one-time MARCXML → Pinecone pipeline

### Data model stored in Pinecone
Each vector has metadata: `term`, `preferred`, `is_variant`, `record_id`.  
Field 150 (preferred) and field 450 (variants) from MARC records are both indexed.

## Environment Variables

Copy `.env.example` to `.env.local` and fill in:

| Variable | Purpose |
|---|---|
| `PINECONE_API_KEY` | Pinecone REST API key |
| `PINECONE_INDEX_HOST` | Full host URL for the `authph` index |
| `HF_API_TOKEN` | HuggingFace Inference API token |

## Notes

- The HuggingFace model cold-starts (~20 s); the frontend handles 503 responses with auto-retry.
- Pinecone index: cosine similarity, 384 dimensions, AWS us-east-1, serverless.
- Search queries must use the `"query: "` prefix; indexed passages use `"passage: "` prefix (handled automatically).
