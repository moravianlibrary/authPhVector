# Nový hlodač

Sémantické vyhledávání záznamů v Národních autoritách České republiky.

Cíl: Nástroj, který má pomoci badatelům a knihovníkům vyhledávat relevantní záznamy v Národních autoritách ČR. Ověření koncepce předzpracování vyhledávacích termínů v knihovních katalozích.

## Nastavení
```bash
cp .env.example .env.local  # Vytvoří .env.local
edit .env.local             # Nastavení proměnných
```

## Příkazy pro vývoj
```bash
npm run dev          # Start development server (localhost:3000)
npm run lint         # ESLint via Next.js
npx tsc --noEmit     # TypeScript type check without emitting files
shellcheck bin/*.sh  # Lint shell scripts with ShellCheck
```

## Příkazy pro práci s daty
```bash
bin/setup_venv.sh    # Připraví virtuální prostředí pro běh python skriptů
bin/download_data.sh # Stáhne data potřebná pro indexování. Většina dat se nestahuje znovu, pokud soubory už na disku exitují
bin/run_indexing.sh  # Spustí indexování záznamů do Pinecone (pouřijte parametr --help pro podrobnější informace)
bin/clean_data.sh    # Odstraní data potřebná pro indexování (skript download_data je pak všechny aktualizuje)
```
