import { NextRequest, NextResponse } from "next/server";

const PINECONE_INDEX_HOST = process.env.PINECONE_INDEX_HOST!;
const PINECONE_API_KEY = process.env.PINECONE_API_KEY!;
const HF_API_TOKEN = process.env.HF_TOKEN!;
const HF_MODEL_URL =
  "https://api-inference.huggingface.co/models/intfloat/multilingual-e5-small";

export interface SearchResult {
  recordId: string;
  preferredTerm: string;
  matchedTerm: string;
  isVariant: boolean;
  score: number;
}

async function embedQuery(query: string): Promise<number[]> {
  // e5 modely vyžadují prefix "query: " pro vyhledávací dotazy
  const res = await fetch(HF_MODEL_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${HF_API_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ inputs: `query: ${query}` }),
  });

  if (res.status === 503) {
    const json = await res.json();
    const estimatedTime: number = json.estimated_time ?? 20;
    throw Object.assign(new Error("model_loading"), { estimatedTime });
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HuggingFace API error ${res.status}: ${text}`);
  }

  const data = await res.json();
  // HF Inference vrací [[...384 čísel...]] pro sentence-transformers
  return Array.isArray(data[0]) ? (data[0] as number[]) : (data as number[]);
}

async function queryPinecone(
  vector: number[],
  topK: number
): Promise<{ matches: Array<{ score: number; metadata: Record<string, unknown> }> }> {
  const res = await fetch(`${PINECONE_INDEX_HOST}/query`, {
    method: "POST",
    headers: {
      "Api-Key": PINECONE_API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ vector, topK, includeMetadata: true }),
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
  const topK: number = Math.min(Math.max(Number(body.topK) || 10, 1), 50);

  if (!query) {
    return NextResponse.json({ error: "Prázdný dotaz" }, { status: 400 });
  }

  try {
    const vector = await embedQuery(query);
    // Načteme více výsledků než potřebujeme, abychom měli zásobu po deduplikaci
    const raw = await queryPinecone(vector, topK * 3);

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
      };
      if (seen.has(meta.preferred)) continue;
      seen.add(meta.preferred);

      results.push({
        recordId: meta.record_id,
        preferredTerm: meta.preferred,
        matchedTerm: meta.term,
        isVariant: Boolean(meta.is_variant),
        score: Math.round(match.score * 1000) / 1000,
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
    return NextResponse.json({ error: "Vyhledávání selhalo" }, { status: 500 });
  }
}
