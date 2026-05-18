import { NextResponse } from "next/server";

const HF_MODEL_URL =
  "https://router.huggingface.co/hf-inference/models/intfloat/multilingual-e5-small/pipeline/feature-extraction";

export async function GET() {
  const results: Record<string, unknown> = {};

  // 1. Check env vars presence (never expose values)
  results.env = {
    PINECONE_API_KEY: !!process.env.PINECONE_API_KEY,
    PINECONE_INDEX_HOST: !!process.env.PINECONE_INDEX_HOST,
    HF_TOKEN: !!process.env.HF_TOKEN,
    PINECONE_INDEX_HOST_VALUE: process.env.PINECONE_INDEX_HOST
      ? process.env.PINECONE_INDEX_HOST.replace(/\/+$/, "") // strip trailing slash
      : null,
  };

  // 2. Test HuggingFace embedding
  try {
    const hfRes = await fetch(HF_MODEL_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.HF_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ inputs: "query: test" }),
    });
    const hfText = await hfRes.text();
    let hfBody: unknown;
    try { hfBody = JSON.parse(hfText); } catch { hfBody = hfText.slice(0, 300); }
    results.hf = {
      status: hfRes.status,
      ok: hfRes.ok,
      responseType: Array.isArray(hfBody)
        ? Array.isArray((hfBody as unknown[])[0])
          ? `nested array [${(hfBody as unknown[]).length}][${((hfBody as number[][])[0]).length}]`
          : `flat array [${(hfBody as unknown[]).length}]`
        : typeof hfBody,
      error: hfRes.ok ? null : hfBody,
    };
  } catch (e: unknown) {
    results.hf = { error: String(e) };
  }

  // 3. Test Pinecone connectivity
  const host = (process.env.PINECONE_INDEX_HOST ?? "").replace(/\/+$/, "");
  try {
    const pcRes = await fetch(`${host}/describe_index_stats`, {
      method: "POST",
      headers: {
        "Api-Key": process.env.PINECONE_API_KEY ?? "",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    });
    const pcBody = await pcRes.json();
    results.pinecone = {
      status: pcRes.status,
      ok: pcRes.ok,
      totalVectorCount: pcBody.totalVectorCount ?? pcBody.total_vector_count ?? null,
      error: pcRes.ok ? null : pcBody,
    };
  } catch (e: unknown) {
    results.pinecone = { error: String(e) };
  }

  return NextResponse.json(results);
}
