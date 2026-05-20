import { NextRequest, NextResponse } from "next/server";

const PINECONE_INDEX_HOST = process.env.PINECONE_INDEX_HOST!;
const PINECONE_API_KEY = process.env.PINECONE_API_KEY!;
const HF_API_TOKEN = process.env.HF_TOKEN!;

const ALLOWED_MODELS = new Set(["intfloat/multilingual-e5-small"]);
const DEFAULT_MODEL = "intfloat/multilingual-e5-small";

export interface SearchResult {
  recordId: string;
  preferredTerm: string;
  matchedTerm: string;
  isVariant: boolean;
  score: number;
  mdt: string[];
  konspekt: string[];
  authorityUrl: string;
  source: string;
}

async function embedQuery(query: string, modelId: string): Promise<number[]> {
  const url = `https://router.huggingface.co/hf-inference/models/${modelId}/pipeline/feature-extraction`;
  // e5 modely vyžadují prefix "query: " pro vyhledávací dotazy
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${HF_API_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ inputs: `query: ${query}` }),
  });

  // Číst jako text nejdříve — HF může vrátit HTML při auth chybách
  const text = await res.text();

  if (res.status === 503) {
    let estimatedTime = 20;
    try {
      const json = JSON.parse(text);
      estimatedTime = json.estimated_time ?? 20;
    } catch {}
    throw Object.assign(new Error("model_loading"), { estimatedTime });
  }

  if (!res.ok) {
    throw Object.assign(new Error(`hf_error`), {
      detail: `HuggingFace ${res.status}: ${text.slice(0, 300)}`,
    });
  }

  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw Object.assign(new Error(`hf_error`), {
      detail: `HuggingFace vrátil neplatný JSON: ${text.slice(0, 200)}`,
    });
  }

  // HF Inference vrací [[...384 čísel...]] nebo [...384 čísel...]
  if (Array.isArray(data)) {
    return Array.isArray((data as unknown[])[0])
      ? ((data as number[][])[0])
      : (data as number[]);
  }
  throw Object.assign(new Error(`hf_error`), {
    detail: `Neočekávaný formát odpovědi: ${JSON.stringify(data).slice(0, 200)}`,
  });
}

async function queryPinecone(
  vector: number[],
  topK: number,
  filter?: Record<string, unknown>
): Promise<{ matches: Array<{ score: number; metadata: Record<string, unknown> }> }> {
  const res = await fetch(`${PINECONE_INDEX_HOST}/query`, {
    method: "POST",
    headers: {
      "Api-Key": PINECONE_API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ vector, topK, includeMetadata: true, ...(filter ? { filter } : {}) }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Pinecone error ${res.status}: ${text}`);
  }

  return res.json();
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const query: string = (body.query ?? "").trim();
  const topK: number = Math.min(Math.max(Number(body.topK) || 10, 1), 100);
  const source: string = (body.source ?? "").trim();
  const rawModel: string = (body.model ?? "").trim();
  const modelId = ALLOWED_MODELS.has(rawModel) ? rawModel : DEFAULT_MODEL;

  if (!query) {
    return NextResponse.json({ error: "Prázdný dotaz" }, { status: 400 });
  }

  const filter = source ? { source: { "$eq": source } } : undefined;

  try {
    const vector = await embedQuery(query, modelId);
    // Načteme více výsledků než potřebujeme, abychom měli zásobu po deduplikaci
    const raw = await queryPinecone(vector, topK * 3, filter);

    // Deduplikace: ze shodné autority (stejný preferred term) ponecháme
    // pouze nejlépe skórující shodu, ať už šlo o preferred nebo variant.
    const seen = new Set<string>();
    const results: SearchResult[] = [];

    for (const match of raw.matches ?? []) {
      const meta = match.metadata as {
        preferred: string;
        term: string;
        is_variant: boolean;
        record_id: string;
        mdt: string;
        konspekt: string;
        authority_url: string;
        source: string;
      };
      if (seen.has(meta.preferred)) continue;
      seen.add(meta.preferred);

      results.push({
        recordId: meta.record_id,
        preferredTerm: meta.preferred,
        matchedTerm: meta.term,
        isVariant: Boolean(meta.is_variant),
        score: Math.round(match.score * 1000) / 1000,
        mdt: meta.mdt ? meta.mdt.split("|").filter(Boolean) : [],
        konspekt: meta.konspekt ? meta.konspekt.split("|").filter(Boolean) : [],
        authorityUrl: meta.authority_url ?? "",
        source: meta.source ?? "",
      });

      if (results.length >= topK) break;
    }

    return NextResponse.json({ results });
  } catch (err: unknown) {
    const e = err as Error & { estimatedTime?: number };
    if (e.message === "model_loading") {
      return NextResponse.json(
        { error: "model_loading", retryAfter: e.estimatedTime ?? 20 },
        { status: 503 }
      );
    }
    console.error("[/api/search]", e);
    const detail = (e as Error & { detail?: string }).detail;
    return NextResponse.json(
      { error: detail ?? "Vyhledávání selhalo" },
      { status: 500 }
    );
  }
}
