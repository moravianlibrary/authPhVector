# Nový hlodač

## Project Context

Semantic search over Czech National Authority File (Národní autority ČR) records.
Goal: Tool to help researchers and librarians find relevant records in the Národní autority ČR. Proof of concept of library catalog serch term preprocessing.~~

## Build & run
- Running on local machine: `npm run dev`
- After typescript files changes run: `npx tsc --noEmit` a `npm run lint`
- After shell scripts changes run: `shellcheck bin/*.sh`

## Codebase
- Use semantic versioning, after every change update package.json version and commit

## Don't
- Don't add new dependencies without asking.
- If you are not sure about something, ask.

## Documentation
- For every new feature add documentation file to docs/features/.
- For every architectural decision (choice of library, pattern), create an entry in docs/decisions/. Use the MADR format.
- For changes in code look at file docs/api.md and update it if needed.
- The documentation explains WHY, not WHAT. I can see what the code does by looking at the code itself.
- Při každé změně aktualizuj relevantní soubory v docs/.

## Change log
- Before making any change that alters the behavior or structure of the code, make a brief note in docs/log/.
- The record includes: date, file, description of the change, the request it responds to, and the source of the request.
- The changelog entries are sorted by date, latest first.
- Use format "Keep a Changelog"
- Při každé aktualizaci docs/log/CHANGELOG.md také aktualizuj CHANGELOG.md v kořeni repozitáře. Tento soubor je zobrazován uživatelům přímo v aplikaci — piš jej jednoduchou češtinou bez odkazů na jiné soubory, bez názvů souborů a commit hashů.

