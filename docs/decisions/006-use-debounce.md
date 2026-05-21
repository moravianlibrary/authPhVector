# ADR 006 — Knihovna `use-debounce` pro debouncing vstupu

**Status:** Accepted  
**Datum:** 2026-05-18

## Context

Vyhledávací pole spouští dotaz na backend při každé změně vstupu. Bez debouncingu by každý stisk klávesy vyvolal volání HuggingFace API a Pinecone, což způsobuje zbytečnou zátěž a zdržení (každý dotaz trvá ~500 ms).

Potřebujeme debouncing — odložit spuštění vyhledávání o ~400 ms po posledním stisku klávesy.

## Alternativy

1. **Vlastní `useRef` + `setTimeout`** — standardní React vzor, žádná závislost. Nevýhoda: nutnost ručně spravovat timer a cleanup v `useCallback`.
2. **`lodash.debounce`** — de-facto standard, ale přidává ~70 kB (nebo nutnost tree-shakingu) pro jednu funkci.
3. **`use-debounce`** — dedikovaná React hook knihovna (<2 kB), poskytuje `useDebouncedCallback` s integrovaným cleanup při unmount.

## Decision

Použit `use-debounce` (`useDebouncedCallback`).

## Důvod

`use-debounce` je minimální závislost navržená přímo pro React hooks. Oproti vlastní implementaci eliminuje boilerplate pro cleanup a oproti lodash je výrazně menší. Pro tento use-case (jedno vyhledávací pole) je to proporcionální volba.
