# API Reference

## POST /api/search

Performs semantic search over the Czech National Authority File (Národní autority ČR). The query is converted to a vector embedding via the HuggingFace Inference API and matched against pre-indexed authority records in Pinecone using cosine similarity.

### Request

**Content-Type:** `application/json`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | yes | — | Search term. Must be non-empty after trimming. |
| `topK` | number | no | `10` | Number of results to return. Clamped to the range `[1, 100]`. |
| `source` | string | no | `""` | Filter results by record type. See [Source values](#source-values). |
| `model` | string | no | `intfloat/multilingual-e5-small` | Embedding model ID. See [Available models](#available-models). Unknown values fall back to the default model. |

#### Example request

```json
{
  "query": "životopis",
  "topK": 5,
  "source": "ph",
  "model": "intfloat/multilingual-e5-small"
}
```

```bash
curl -X POST https://authphvector.vercel.app/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "životopis", "topK": 5}'
```

### Response

#### 200 OK

Returns a JSON object with a `results` array. Results are deduplicated by preferred term — when multiple indexed variants point to the same authority record, only the highest-scoring match is returned.

```json
{
  "results": [
    {
      "recordId": "ph123456",
      "preferredTerm": "Životopisy",
      "matchedTerm": "životopis",
      "isVariant": true,
      "score": 0.923,
      "mdt": ["929"],
      "konspekt": ["12 - Životopisy"],
      "authorityUrl": "https://aleph.nkp.cz/...",
      "source": "ph"
    }
  ]
}
```

#### Result object fields

| Field | Type | Description |
|-------|------|-------------|
| `recordId` | string | Authority record identifier (MARC 001 field). |
| `preferredTerm` | string | The canonical (preferred) form of the authority term. |
| `matchedTerm` | string | The specific term that produced the match — either the preferred term or a variant. |
| `isVariant` | boolean | `true` if the match was found via a variant term (MARC 450/451/455/490), `false` if via the preferred term. |
| `score` | number | Cosine similarity score in the range `[0, 1]`, rounded to 3 decimal places. Higher is more similar. |
| `mdt` | string[] | MDT (Universal Decimal Classification) codes from MARC 080, if present. |
| `konspekt` | string[] | Konspekt subject category labels from MARC 072, if present. |
| `authorityUrl` | string | URL to the authority record in the national catalogue (from MARC 998), if present. |
| `source` | string | Record type identifier. See [Source values](#source-values). |

### Error responses

#### 400 Bad Request — empty query

```json
{ "error": "Prázdný dotaz" }
```

#### 503 Service Unavailable — embedding model loading

Returned when the HuggingFace model is cold-starting. The client should retry after the indicated delay.

```json
{
  "error": "model_loading",
  "retryAfter": 20
}
```

| Field | Type | Description |
|-------|------|-------------|
| `error` | `"model_loading"` | Fixed string identifying the condition. |
| `retryAfter` | number | Suggested wait time in seconds before retrying. |

#### 500 Internal Server Error

```json
{ "error": "<error detail message>" }
```

Returned for HuggingFace inference failures, Pinecone errors, or unexpected conditions. The `error` field contains a human-readable description.

---

## Source values

The `source` field identifies the type of authority record. Use it both as a request filter and to interpret results.

| Value | Record type |
|-------|-------------|
| `ph` | Předmětové heslo (Subject heading) |
| `ge` | Geografický termín (Geographic name) |
| `sk` | Konspekt (Subject category) |
| `fd` | Formální deskriptor (Form/genre term) |

Omitting `source` (or passing an empty string) searches across all record types.

---

## Available models

Models are configured in [`config/models.json`](../config/models.json). The following models are currently available:

| Model ID | Dimensions | Description |
|----------|-----------|-------------|
| `intfloat/multilingual-e5-small` | 384 | Default. Fast, multilingual, uses `query:` / `passage:` prefixes. |
| `intfloat/multilingual-e5-large` | 1024 | Higher quality, same E5 family, slower cold start. |
| `BAAI/bge-m3` | 1024 | Multilingual BGE-M3, no prefixes required. |

Pass the model ID in the `model` request field. Unknown model IDs silently fall back to `intfloat/multilingual-e5-small`. Results from different models are **not comparable** — each model uses its own Pinecone index.

---

## Notes

- **Cold starts:** HuggingFace serverless inference models may take ~20 seconds to load after a period of inactivity. The frontend handles this automatically via the `503 / model_loading` retry mechanism.
- **Deduplication:** The API fetches `topK × 3` raw candidates from Pinecone and deduplicates by preferred term before returning `topK` results. This ensures that variant-term matches do not crowd out results from different authority records.
- **Score interpretation:** Scores are cosine similarities. Values above `0.75` indicate high semantic similarity; values below `0.5` are weak matches.
