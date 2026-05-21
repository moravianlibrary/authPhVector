import { NextResponse } from "next/server";
import { InferenceClient } from "@huggingface/inference";
import modelsConfig from "../../../../config/models.json";

const MODEL_CONFIG = modelsConfig.models as Record<string, {
  indexHostEnv: string;
  queryPrefix: string;
  provider?: string;
}>;

export async function GET() {
  const results: Record<string, unknown> = {};

  // 1. Check env vars presence (never expose values)
  results.env = {
    PINECONE_API_KEY: !!process.env.PINECONE_API_KEY,
    HF_TOKEN: !!process.env.HF_TOKEN,
    ...Object.fromEntries(
      Object.entries(MODEL_CONFIG).map(([id, cfg]) => [
        cfg.indexHostEnv,
        !!process.env[cfg.indexHostEnv],
      ])
    ),
  };

  // 2. Test HuggingFace embedding (default model)
  const defaultModelId = modelsConfig.defaultModel;
  const defaultCfg = MODEL_CONFIG[defaultModelId];
  try {
    const hf = new InferenceClient(process.env.HF_TOKEN);
    const result = await hf.featureExtraction({
      model: defaultModelId,
      inputs: `${defaultCfg.queryPrefix}test`,
      ...(defaultCfg.provider ? { provider: defaultCfg.provider as import("@huggingface/inference").InferenceProviderOrPolicy } : {}),
    });
    const flat = Array.isArray(result)
      ? Array.isArray((result as unknown[])[0])
        ? (result as number[][])[0]
        : (result as number[])
      : null;
    results.hf = {
      model: defaultModelId,
      ok: flat !== null,
      dimensions: flat?.length ?? null,
    };
  } catch (e: unknown) {
    results.hf = { model: defaultModelId, ok: false, error: String(e) };
  }

  // 3. Test Pinecone connectivity (default model's index)
  const host = (process.env[defaultCfg.indexHostEnv] ?? "").replace(/\/+$/, "");
  if (host) {
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
        index: defaultCfg.indexHostEnv,
        ok: pcRes.ok,
        totalVectorCount: pcBody.totalVectorCount ?? pcBody.total_vector_count ?? null,
        error: pcRes.ok ? null : pcBody,
      };
    } catch (e: unknown) {
      results.pinecone = { index: defaultCfg.indexHostEnv, ok: false, error: String(e) };
    }
  } else {
    results.pinecone = { index: defaultCfg.indexHostEnv, ok: false, error: `${defaultCfg.indexHostEnv} není nastavena` };
  }

  return NextResponse.json(results);
}
