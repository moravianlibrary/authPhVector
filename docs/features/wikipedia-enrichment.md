# Obohacení embeddingů Wikipedia obsahem

## Proč

Autoritní záznamy jsou záměrně stručné: preferovaný termín, varianta nebo dvě, MDT kód. Samotný text „Aeromechanika" je sémanticky chudý — embedding modelu neřekne téměř nic o tom, co tento obor zahrnuje.

Kvalitní embedding vyžaduje kontext. Wikipedia články poskytují definice, synonyma, příbuzné pojmy a příklady v přirozeném jazyce. Přidání prvních odstavců článku k termínu při indexaci výrazně rozšíří sémantické pokrytí: dotaz „mechanika tekutin" najde záznam „Aeromechanika" proto, že Wikipedii článek o aeromechanice mechaniku tekutin zmiňuje.

## Jak to funguje

1. `bin/download_data.sh` stáhne multistream dump české Wikipedie a `redirect.txt`.
2. `scripts/fetch_wiki.py` načte z dump souboru (bez jeho úplného rozbalení, přes byte-offset index) text pro každý záznam, jehož preferovaný termín odpovídá názvu Wikipedia článku nebo přesměrování.
3. `scripts/index_vectors.py` konkatenuje MARC termín + Wikipedia text a tento rozšířený text indexuje.

Příznak `--no-wiki` přeskočí krok 3 — užitečné při ladění nebo reindexaci bez Wikipedia dat.

## Proč lokální dump místo API

Online fetching přes MediaWiki API by při 40–50 tisících záznamů trval hodiny a byl by omezen rate limity. Lokální multistream dump umožňuje extrakci přes byte-offset index — konkrétní článek se najde bez rozbalení celého 1,3GB souboru.

## Relevantní soubory

- `scripts/fetch_wiki.py` — extrakce Wikipedia článků z lokálního dumpu
- `scripts/index_vectors.py` — integrace Wikipedia textu do embeddingů
- `bin/download_data.sh` — stažení Wikipedia dumpu
- `data/wiki/` — extrahované texty článků (generované, nejsou v gitu)
