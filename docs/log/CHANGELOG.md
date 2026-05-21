# Changelog

Všechny podstatné změny projektu jsou dokumentovány zde.

Formát: [Keep a Changelog](https://keepachangelog.com/cs/1.0.0/)  
Verzování: [Semantic Versioning](https://semver.org/)

Každý záznam obsahuje: datum, dotčené soubory, popis změny, jaký požadavek řeší a zdroj (commit).

---

## [0.2.0] — 2026-05-21

### 2026-05-21

#### Fixed
- **`bin/download_data.sh`** — přidáno `set -euo pipefail`; selhání wget/gunzip nyní ukončí skript místo tichého pokračování.  
  Požadavek: výpadek sítě nebo chyba komprese zapisoval poškozený soubor bez varování.  
  Zdroj: code review

- **`bin/download_data.sh`** — pipeline pro stažení `redirect.txt` zapisuje přes dočasný soubor; přejmenování proběhne jen po úspěchu.  
  Požadavek: při selhání pipeline se vytvořil prázdný/poškozený `redirect.txt`, který pak existence-check považoval za platný a přeskočil opětovné stažení.  
  Zdroj: code review

- **`scripts/index_vectors.py`** — načítání `config/models.json` obaleno do `try/except`; chybějící nebo poškozený soubor vypíše čitelnou chybovou hlášku místo Python traceback.  
  Požadavek: chyba konfigurace se projevila jako nečitelný traceback při importu modulu.  
  Zdroj: code review

---

## [0.1.0] — 2026-05-18

### 2026-05-21

#### Added
- **ESLint konfigurace** — `eslint`, `eslint-config-next`, `.eslintrc.json`  
  Požadavek: statická analýza TypeScript/JSX kódu před každým commitem.  
  Zdroj: commity `4cb113a`, `08832ea`

- **README.md** — setup instrukce a vývojové příkazy v češtině.  
  Požadavek: nový přispěvatel potřebuje vědět, jak projekt spustit.  
  Zdroj: commit `49ee6f3`

- **docs/api.md** — anglická API reference pro `/api/search`.  
  Požadavek: zdokumentovat veřejné rozhraní aplikace.  
  Zdroj: commit `65f51d6`

- **config/models.json** — centralizovaná konfigurace embedding modelů.  
  Požadavek: Next.js i Python indexovací skript četly konfiguraci ze dvou různých míst; přidání nového modelu znamenalo editaci obou.  
  Zdroj: commit `91e2a3f`  
  Viz: [ADR 005](../decisions/005-centralized-model-config.md)

- **Model BAAI/bge-m3** — třetí embedding model (1024-dim, bez prefixů).  
  Soubory: `config/models.json`, `scripts/index_vectors.py`  
  Požadavek: experimentální srovnání s E5 rodinou; BGE-M3 nevyžaduje query/passage prefixy.  
  Zdroj: commit `2e41173`

- **Příznak `--no-wiki`** pro `scripts/index_vectors.py` — přeskočí Wikipedia data při indexaci.  
  Požadavek: při vývoji a ladění je rychlejší indexovat pouze MARC záznamy.  
  Zdroj: commit `25a9399`

- **Vercel Web Analytics** — `@vercel/analytics`, `src/app/layout.tsx`  
  Sledování návštěvnosti a page views prostřednictvím Vercel Analytics.  
  Požadavek: základní přehled o využití aplikace bez nutnosti vlastní infrastruktury.  
  Zdroj: commity `3896294`, `86d7eb8`

#### Changed
- **URL parametr dotazu**: z URL fragmentu (`#výraz`) na query param (`?q=výraz`).  
  Soubory: `src/app/page.tsx`  
  Požadavek: `#fragment` server nevidí (nelze logovat, sdílet přes OG), `?q=` je standardní a sdílitelný. Zpětná kompatibilita: URL s fragmentem se automaticky přesměruje.  
  Zdroj: commit `c4c01db`

- **CLAUDE.md** — přestrukturováno pro srozumitelnost; doplněny dokumentační požadavky.  
  Zdroj: commit `e81313f`

---

### 2026-05-20

#### Added
- **GPU podpora v `scripts/index_vectors.py`** — PyTorch s CUDA 12.4 v `requirements.txt`; auto-detekce nebo manuální `--device` příznak.  
  Požadavek: indexace stovek tisíc záznamů na CPU trvá hodiny; GPU ji zkrátí na minuty.  
  Zdroj: commit `2613461`

- **Model `intfloat/multilingual-e5-large`** — 1024-dim varianta E5, vyšší kvalita embeddingů než small.  
  Soubory: `src/app/page.tsx`, `src/app/api/search/route.ts`, `scripts/index_vectors.py`  
  Požadavek: model Qwen3 měl status "error" na HF Inference; E5-large je stabilní alternativa vyšší kvality.  
  Zdroj: commity `fa01755`, `3b0e9de`  
  Viz: [feature/multiple-models](../features/multiple-models.md)

- **`InferenceClient` z `@huggingface/inference`** místo ručního `fetch`.  
  Soubory: `src/app/api/search/route.ts`, `package.json`  
  Požadavek: knihovna automaticky resolví endpoint pro každý model a zpracovává `model_loading` stav; ručně napsaný fetch to dělal nesprávně.  
  Zdroj: commit `50abf54`

- **Dropdown pro výběr embedding modelu** v UI.  
  Soubory: `src/app/page.tsx`  
  Požadavek: uživatel potřebuje přepínat mezi modely bez změny URL ručně.  
  Zdroj: commit `1cda9f6`

- **Synchronizace modelu do URL** (`?model=`).  
  Soubory: `src/app/page.tsx`  
  Požadavek: sdílení odkazu se zachovaným výběrem modelu.  
  Zdroj: commit `cc3d230`

- **`bin/clean_data.sh`** — smaže stažená data a umožní čerstvé stažení.  
  Požadavek: po přidání nového zdroje dat je nutné přeindexovat od nuly.  
  Zdroj: commit `7224198`

- **Typ záznamu `fd` (Formální deskriptor)** — čtvrtý typ autoritního záznamu.  
  Soubory: `src/app/page.tsx`, `scripts/index_vectors.py`, `bin/download_data.sh`  
  Požadavek: formální/žánrové deskriptory jsou oddělená entita od věcných hesel.  
  Zdroj: commit `6ea00a5`  
  Viz: [feature/authority-record-types](../features/authority-record-types.md)

- **Filtrování podle typu záznamu** — chip buttony (ph / ge / sk / fd / Vše).  
  Soubory: `src/app/page.tsx`, `src/app/globals.css`  
  Požadavek: uživatel chce prohledávat jen konkrétní typ autority.  
  Zdroj: commit `a882913`

- **Synchronizace source filtru do URL** (`?source=`).  
  Soubory: `src/app/page.tsx`  
  Zdroj: commit `664dd92`

- **Indexace `aut_sk.xml`** (Konspekt) se složeným preferred termem z polí 190$a–$x.  
  Soubory: `scripts/index_vectors.py`, `bin/download_data.sh`  
  Požadavek: Konspekt záznamy mají víceúrovňová hesla; concatenace podpolí dává smysluplný embedding vstup.  
  Zdroj: commit `76873ce`

- **Automatická generace `redirect.txt`** z Wikipedia SQL dumpu.  
  Soubory: `scripts/parse_redirect_sql.py`, `bin/download_data.sh`  
  Požadavek: dříve bylo nutné redirect soubor generovat ručně.  
  Zdroj: commit `45feaf8`

#### Changed
- **Shell skripty přesunuty z `scripts/` do `bin/`**.  
  Požadavek: oddělit spustitelné skripty (bin/) od Python kódu (scripts/).  
  Zdroj: commit `39f2d4a`

- **Přejmenování aplikace** na „Nový hlodač" a aktualizace tagline.  
  Soubory: `src/app/page.tsx`  
  Zdroj: commit `6f1bc94`

- **Barevné odlišení source badge** podle typu záznamu (ph/ge/sk).  
  Soubory: `src/app/page.tsx`, `src/app/globals.css`  
  Požadavek: vizuální rozlišení typů na první pohled bez čtení textu.  
  Zdroj: commit `6aba7d3`

- **Automatické načítání `.env.local`** v `bin/run_indexing.sh`.  
  Požadavek: uživatel nemusí ručně exportovat proměnné prostředí.  
  Zdroj: commit `1a27f9b`

#### Fixed
- TypeScript chyba v debug logování.  
  Soubory: `src/app/api/debug/route.ts`  
  Zdroj: commit `8eca6e0`

- Source filter chips: klíče derivovány z `SOURCE_LABELS` místo pevně zadaných.  
  Zdroj: commit `2ea9351`

- Cesty v bin/ skriptech po přesunu z scripts/.  
  Zdroj: commit `84e56c1`

---

### 2026-05-19

#### Added
- **Obohacení embeddingů Wikipedia obsahem** — `scripts/fetch_wiki.py` načte text článku pro každý autoritní záznam a přidá ho do indexovaného textu.  
  Soubory: `scripts/fetch_wiki.py`, `scripts/index_vectors.py`  
  Požadavek: samotný MARC termín je krátký; Wikipedia text přidává sémantický kontext a zlepšuje pokrytí synonym.  
  Zdroj: commit `ce8a842`  
  Viz: [feature/wikipedia-enrichment](../features/wikipedia-enrichment.md)

- **URL záznamu** (MARC pole 998$a) v metadatech a výsledcích vyhledávání.  
  Soubory: `scripts/index_vectors.py`, `src/app/api/search/route.ts`, `src/app/page.tsx`  
  Požadavek: uživatel potřebuje přejít přímo na záznam v národním katalogu.  
  Zdroj: commit `8ed4687`

- **Logo a favicon**.  
  Soubory: `public/logo.svg`, `src/app/layout.tsx`  
  Zdroj: commit `aaf8d1e`

- **Clear button** pro vyhledávací pole.  
  Soubory: `src/app/page.tsx`  
  Zdroj: commit `3edf2c0`

- **Výběr počtu výsledků** (10 / 20 / 50 / 100).  
  Soubory: `src/app/page.tsx`  
  Požadavek: různé use-cases vyžadují různý počet výsledků (rychlý přehled vs. kompletní soupis).  
  Zdroj: commit `b02162a`

- **MDT kódy** (UDC, MARC 080$a) v metadatech a výsledcích, s copy buttonem.  
  Soubory: `scripts/index_vectors.py`, `src/app/api/search/route.ts`, `src/app/page.tsx`  
  Požadavek: MDT je hlavní klasifikační schéma ČNK; knihovník potřebuje MDT kód pro katalogizaci.  
  Zdroj: commity `84476d5`, `32801bf`

- **Konspekt kategorie** (MARC 072) v metadatech a výsledcích, s copy buttonem.  
  Soubory: `scripts/index_vectors.py`, `src/app/api/search/route.ts`, `src/app/page.tsx`  
  Požadavek: Konspekt je používán v českém knihovnickém prostředí pro tematické zařazení.  
  Zdroj: commit `d8366df`

- **Copy-to-clipboard buttony** u preferovaného termínu, ID záznamu, URL, MDT a Konspekt.  
  Soubory: `src/app/page.tsx`, `src/app/globals.css`  
  Požadavek: knihovníci kopírují nalezené termíny a kódy do katalogizačních systémů; copy button eliminuje ruční označování textu.  
  Zdroj: commity `d8faf59`, `edcbb17`  
  Viz: [feature/copy-to-clipboard](../features/copy-to-clipboard.md)

- **`scripts/fetch_wiki.py`** — fetcher Wikipedia obsahu (původně přes HTTP, přepsán na lokální dump).  
  Požadavek: online fetching byl pomalý a nespolehlivý; lokální multistream dump umožňuje extrakci tisíců článků za minuty.  
  Zdroj: commity `4788c6f`, `e01cd1f`

- **`bin/setup_venv.sh`** — standalone skript pro setup Python venv.  
  Zdroj: commit `522be05`

- **`.vercelignore`** — velká datová a Python soubory jsou vyloučena z Vercel deploye.  
  Požadavek: data/ (~1.6 GB) a scripts/.venv by prodloužily deploy a překročily limity.  
  Zdroj: commit `4d6af3b`

#### Changed
- **Karta výsledku** přestrukturována do řádků s popisky (ID, Záznam, MDT, Konspekt).  
  Soubory: `src/app/page.tsx`, `src/app/globals.css`  
  Zdroj: commit `1843f45`

- **Synchronizace dotazu do URL fragmentu** (předchůdce ?q= parametru).  
  Soubory: `src/app/page.tsx`  
  Zdroj: commit `be26acc`

---

### 2026-05-18

#### Added
- **Počáteční verze aplikace** — sémantické vyhledávání přes Pinecone + HuggingFace Inference API, React UI s Next.js.  
  Soubory: `src/app/page.tsx`, `src/app/api/search/route.ts`, `src/app/layout.tsx`, `src/app/globals.css`, `package.json`, `next.config.ts`, `tsconfig.json`  
  Požadavek: ověření koncepce sémantického vyhledávání nad Národními autoritami ČR.  
  Zdroj: commit `7429aac`  
  Viz: [feature/semantic-search](../features/semantic-search.md)

- **`/api/debug` endpoint** — diagnostika připojení k HuggingFace a Pinecone.  
  Soubory: `src/app/api/debug/route.ts`  
  Požadavek: rychlá diagnostika při problémech s produkcí bez nutnosti přístupu k logům.  
  Zdroj: commit `ee36650`

- **`scripts/index_vectors.py`** — MARCXML parser + embedding generátor + Pinecone uploader.  
  Požadavek: jednoúčelový skript pro (re)indexaci autoritních záznamů do vektorové databáze.  
  Zdroj: commit `7429aac`

- **`bin/download_data.sh`** — stažení MARCXML souborů z aleph.nkp.cz a Wikipedia dumpu.  
  Požadavek: reprodukovatelné stažení dat bez ručního kopírování URL.  
  Zdroj: commity `671fccc`, `f8839ad`

- **`vercel.json`** — deklarace Next.js frameworku pro Vercel.  
  Zdroj: commit `eecf8de`

- **Podpora více MARCXML souborů** v indexovacím skriptu.  
  Soubory: `scripts/index_vectors.py`  
  Požadavek: různé typy záznamů jsou v samostatných souborech (aut_ph.xml, aut_ge.xml…).  
  Zdroj: commit `ac957ae`
