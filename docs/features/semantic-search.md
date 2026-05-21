# Sémantické vyhledávání

## Proč

Autoritní záznamy Národní knihovny mají přesně definované preferované termíny (např. „Létadla bojová"). Uživatel — badatel nebo katalogizátor — ale přichází s přirozeným výrazem („stíhačky", „vojenská letadla", „bojové letouny"), který s preferovaným termínem nemusí sdílet ani jedno slovo.

Fulltext nebo prefix-search tento problém neřeší: buď nenajde nic, nebo vrátí nepřesné shody. Potřebujeme vyhledávání podle **věcného smyslu**, ne podle znaků.

Vektorové (sémantické) vyhledávání řeší to tím, že dotaz i dokumenty převede do numerické reprezentace (embedding), kde jsou věcně příbuzné výrazy blízko sebe v geometrickém prostoru. Cosine similarity pak nalezne nejbližší záznamy bez ohledu na konkrétní znění.

## Jak to funguje

1. Při indexaci: každý autoritní termín (preferovaný i variantní) je převeden na embedding a uložen do Pinecone spolu s metadaty záznamu.
2. Při vyhledávání: dotaz uživatele je převeden na embedding, Pinecone vrátí nejbližší vektory, výsledky jsou deduplikovány a seřazeny podle skóre.

Deduplication je nutná, protože jeden autoritní záznam má jeden preferovaný termín, ale může mít mnoho variant — všechny jsou indexovány samostatně. Bez deduplikace by výsledky jednoho záznamu obsadily celou první stránku.

## Relevantní soubory

- `src/app/api/search/route.ts` — vyhledávací endpoint
- `scripts/index_vectors.py` — indexace do Pinecone
- `config/models.json` — konfigurace embedding modelů
