# Copy-to-clipboard tlačítka

## Proč

Cílovou skupinou aplikace jsou knihovníci a katalogizátoři. Ti potřebují nalezené hodnoty přenést do jiného systému — katalogizační aplikace (Aleph, Koha), tabulky, dotaz do OPAC. Přenáší se:

- **Preferovaný termín** — pro pole 600/610/650/651 v MARC záznamu
- **ID záznamu** (MARC 001) — pro propojení $0 / identifikátor autority
- **URL záznamu** — přímý odkaz na záznam v národním katalogu
- **MDT kód** — pro pole 080 v katalogizaci
- **Konspekt** — pro interní poznámky nebo vyhledávací systémy

Bez copy buttonu uživatel musí text ručně označit myší, což je zdlouhavé a náchylné k chybám (obzvlášť u MDT kódů, kde na přesnosti záleží).

## Implementace

Každé tlačítko volá `navigator.clipboard.writeText()` a po úspěchu dočasně zobrazí „✓" místo ikony kopírování. Stav `copiedKey` v komponentě zajistí, že se „✓" zobrazí pouze u naposledy zkopírovaného tlačítka.

## Relevantní soubory

- `src/app/page.tsx` — `handleCopy()`, `copiedKey` state, všechna copy tlačítka
