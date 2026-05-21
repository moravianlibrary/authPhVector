# Feature: Diagnostický endpoint `/api/debug`

## Proč

Při problémech v produkci (model neodpovídá, Pinecone nevrací výsledky) není přístup k serverovým logům vždy okamžitý. Potřebujeme způsob, jak rychle ověřit, zda jsou správně nastaveny klíčové env proměnné a zda jsou dostupné externí služby (HuggingFace, Pinecone) — bez nutnosti nasadit nový kód nebo přistupovat k Vercel dashboardu.

## Co dělá

`GET /api/debug` vrací JSON s diagnostickými informacemi ve třech sekcích:

- **`env`** — přítomnost (true/false) každé env proměnné požadované pro nakonfigurované modely; hodnoty nikdy neexponuje
- **`hf`** — výsledek testovacího embeddingu přes `InferenceClient` s výchozím modelem; vrací počet dimenzí vektoru nebo chybovou zprávu
- **`pinecone`** — výsledek `describe_index_stats` proti Pinecone indexu výchozího modelu; vrací počet vektorů nebo chybovou zprávu

## Poznámky

- Endpoint je veřejně dostupný (bez autentizace) — je vhodný pouze pro produkční diagnostiku, ne pro dlouhodobé monitorování.
- Testuje vždy výchozí model (`defaultModel` z `config/models.json`); přítomnost env proměnných je hlášena pro všechny konfigurované modely.
- Implementováno v `src/app/api/debug/route.ts`, čte konfiguraci z `config/models.json` (viz [ADR 005](../decisions/005-centralized-model-config.md)).
