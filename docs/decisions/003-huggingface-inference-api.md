# ADR 003 — HuggingFace Inference API pro embedding generaci

**Status:** Accepted  
**Datum:** 2026-05-18

## Context

Při každém vyhledávacím dotazu je potřeba převést text na embedding vektor. Model je možné:
1. Hostovat přímo v Next.js API route (ONNX runtime, transformers.js)
2. Hostovat na vlastním serveru (GPU instance)
3. Volat vzdálené API (HuggingFace, OpenAI, Cohere)

Embedding modely jako E5-large mají stovky MB; BAAI/bge-m3 přes 1 GB. Vercel Functions mají limit 50 MB na bundle a timeout 300 s — model v bundlu není možný. Vlastní GPU server by byl příliš nákladný pro proof-of-concept.

## Decision

Zvolíme HuggingFace Inference API přes `@huggingface/inference` knihovnu.

HF poskytuje serverless inference endpoint pro open-source modely — při free tier s potenciálním cold startem (~20 s po nečinnosti). Knihovna `InferenceClient` automaticky resolví endpoint pro každý model, zpracovává chybu `model_loading` a vrací `estimatedTime` pro retry logiku.

API klíč je uložen v prostředí serveru, nikdy nezpracovává prohlížeč.

## Consequences

**Pozitivní:**
- Žádná správa ML infrastruktury
- Jednoduché přidávání nových modelů (jen změna ID v `config/models.json`)
- `model_loading` retry je nativně podporován

**Negativní:**
- Cold start ~20 s po delší nečinnosti (frontendové UI to řeší automatickým retry)
- Latence ~200–500 ms na dotaz (vzdálené volání)
- HF free tier má rate limity
