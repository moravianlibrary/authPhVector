# Podpora více embedding modelů

## Proč

Různé embedding modely nabízejí různé kompromisy mezi rychlostí a kvalitou. Navíc nikdo dopředu neví, který model bude na konkrétní doméně (česká knihovnická terminologie) podávat nejlepší výsledky — závisí to na trénovacích datech, dimenzi prostoru i způsobu prefixování.

Aplikace proto podporuje tři modely a umožňuje přepínat mezi nimi za běhu, aby bylo možné výsledky subjektivně porovnat.

## Proč má každý model vlastní Pinecone index

Embedding vektory různých modelů **nejsou vzájemně porovnatelné** — každý model generuje vektory v jiném prostoru, jiné dimenze, s jinou geometrií. Sdílení jednoho Pinecone indexu by proto dávalo nesmyslné výsledky při přepnutí modelu. Každý model proto má vlastní index, vlastní indexHostEnv a vlastní dimenzionalitu.

## Dostupné modely

| Model | Dimenze | Charakteristika |
|-------|---------|----------------|
| `intfloat/multilingual-e5-small` | 384 | Výchozí. Rychlý, multijazyčný. |
| `intfloat/multilingual-e5-large` | 1024 | Vyšší kvalita, pomalejší cold start. |
| `BAAI/bge-m3` | 1024 | Experimentální; nevyžaduje prefixy. |

E5 modely vyžadují prefixy `query:` / `passage:` — bez nich klesá kvalita. BGE-M3 prefixy nepotřebuje; jejich přidání naopak snižuje výkon.

## Přidání nového modelu

Stačí přidat záznam do `config/models.json` — tento soubor čtou jak Next.js (JSON import), tak Python indexovací skript. Nevyžaduje změny v kódu.

## Relevantní soubory

- `config/models.json` — jediný zdroj pravdy pro konfiguraci modelů
- `src/app/api/search/route.ts` — výběr modelu při query-time
- `scripts/index_vectors.py` — výběr modelu při indexaci
- `src/app/page.tsx` — dropdown pro výběr modelu v UI
