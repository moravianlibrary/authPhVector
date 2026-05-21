# Typy autoritních záznamů

## Proč

Národní autority ČR obsahují čtyři různé typy záznamů, z nichž každý slouží jinému účelu v katalogizaci. Pro uživatele je zásadní, o jaký typ záznamu jde — geografický termín „Praha" má úplně jiné využití než věcné heslo „Praha (motiv)".

Aplikace indexuje všechny čtyři typy do stejného Pinecone indexu (s metadatovým polem `source`) a umožňuje filtrovat výsledky podle typu.

## Typy záznamů

| Kód | Název | MARC soubor | Popis |
|-----|-------|-------------|-------|
| `ph` | Předmětové heslo | `aut_ph.xml` | Věcné termíny pro tematické zpracování dokumentů. Nejpočetnější typ (~40 tisíc záznamů). |
| `ge` | Geografický termín | `aut_ge.xml` | Zeměpisné názvy, regiony, státy (~50 tisíc záznamů). |
| `sk` | Konspekt | `aut_sk.xml` | Hierarchické tematické skupiny, víceúrovňová hesla (190$a–$x). |
| `fd` | Formální deskriptor | `aut_fd.xml` | Formální/žánrové charakteristiky dokumentu (životopis, slovník, atlas…). |

## Proč filtrovat

Bez filtru vyhledávání „Praha" vrátí záznamy z geografických i věcných hesel. Katalogizátor, který hledá geografický termín pro pole 651, chce vidět pouze `ge` záznamy.

## Technická poznámka ke Konspektu

Záznamy Konspektu mají víceúrovňová hesla uložena v podpolích 190$a, $b, $x. Při indexaci jsou tato podpole konkatenována s mezzerou a indexována jako jeden celek — jinak by embedding viděl jen krátkou kategorii bez hierarchického kontextu.

## Relevantní soubory

- `scripts/index_vectors.py` — parsování všech čtyř typů, MARC extrakce
- `bin/download_data.sh` — stažení aut_ph.xml, aut_ge.xml, aut_sk.xml, aut_fd.xml
- `src/app/page.tsx` — chip buttony pro filtrování typu záznamu
- `src/app/api/search/route.ts` — Pinecone filtr podle pole `source`
