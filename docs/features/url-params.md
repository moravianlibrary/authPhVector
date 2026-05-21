# Synchronizace stavu do URL parametrů

## Proč

Vyhledávání má tři proměnné části: dotaz, vybraný model a filter typu záznamu. Bez synchronizace do URL se stav ztratí při obnovení stránky a nelze výsledky sdílet.

Sdílení odkazu je v knihovnickém prostředí běžný pracovní postup: katalogizátor pošle kolegovi odkaz s konkrétním dotazem, výsledkem a vybraným modelem. URL parametry to umožňují bez jakékoli serverové session.

## Parametry

| Parametr | Příklad | Výchozí |
|----------|---------|---------|
| `?q=` | `?q=životopis` | prázdný (žádný dotaz) |
| `?model=` | `?model=intfloat/multilingual-e5-large` | výchozí model z config/models.json |
| `?source=` | `?source=ph` | prázdný (všechny typy) |

## Zpětná kompatibilita

Před přechodem na `?q=` se dotaz ukládal do URL fragmentu (`#životopis`). URL s fragmentem je při prvním načtení automaticky přeložena do `?q=` bez ztráty dotazu — uložené záložky a sdílené odkazy proto stále fungují.

## Relevantní soubory

- `src/app/page.tsx` — tři `useEffect` hooks pro synchronizaci; inicializace ze URL při mount
