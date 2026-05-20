import { NextRequest, NextResponse } from "next/server";
import { InferenceClient } from "@huggingface/inference";

const PINECONE_API_KEY = process.env.PINECONE_API_KEY!;
const HF_API_TOKEN = process.env.HF_TOKEN!;

const DEFAULT_MODEL = "intfloat/multilingual-e5-small";

const MODEL_CONFIG: Record<string, { indexHostEnvVar: string; queryPrefix: string; provider?: string }> = {
  "intfloat/multilingual-e5-small": {
    indexHostEnvVar: "PINECONE_INDEX_HOST",
    queryPrefix: "query: ",
  },
  "intfloat/multilingual-e5-large": {
    indexHostEnvVar: "PINECONE_INDEX_HOST_LARGE",
    queryPrefix: "query: ",
  },
};

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

async function embedQuery(query: string, modelId: string, queryPrefix: string, provider?: string): Promise<number[]> {
  const hf = new InferenceClient(HF_API_TOKEN);
  const result = await hf.featureExtraction({
    model: modelId,
    inputs: `${queryPrefix}${query}`,
    ...(provider ? { provider: provider as import("@huggingface/inference").InferenceProviderOrPolicy } : {}),
  });

  // featureExtraction vrací number[] nebo number[][]
  if (Array.isArray(result)) {
    return Array.isArray((result as unknown[])[0])
      ? ((result as number[][])[0])
      : (result as number[]);
  }
  throw Object.assign(new Error("hf_error"), {
    detail: `Neočekávaný formát odpovědi od HuggingFace`,
  });
}

async function queryPinecone(
  vector: number[],
  topK: number,
  indexHost: string,
  filter?: Record<string, unknown>
): Promise<{ matches: Array<{ score: number; metadata: Record<string, unknown> }> }> {
  const res = await fetch(`${indexHost}/query`, {
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
  const modelId = rawModel in MODEL_CONFIG ? rawModel : DEFAULT_MODEL;
  const cfg = MODEL_CONFIG[modelId];
  const indexHost = process.env[cfg.indexHostEnvVar] ?? "";

  if (!query) {
    return NextResponse.json({ error: "Prázdný dotaz" }, { status: 400 });
  }

  const filter = source ? { source: { "$eq": source } } : undefined;

  try {
    const vector = await embedQuery(query, modelId, cfg.queryPrefix, cfg.provider);
    // Načteme více výsledků než potřebujeme, abychom měli zásobu po deduplikaci
    const raw = await queryPinecone(vector, topK * 3, indexHost, filter);

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
    const detail = (e as Error & { detail?: string }).detail ?? e.message;
    return NextResponse.json(
      { error: detail ?? "Vyhledávání selhalo" },
      { status: 500 }
    );
  }
}
