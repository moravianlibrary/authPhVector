# Feature: Vercel Web Analytics

## Proč

Potřebujeme základní přehled o využití aplikace (počty návštěv, nejčastější dotazy přes URL parametry) bez nutnosti provozovat vlastní analytickou infrastrukturu. Vercel Analytics je integrovaný do platformy, nevyžaduje žádnou konfiguraci na straně serveru a neodesílá data třetím stranám mimo Vercel.

## Co dělá

`@vercel/analytics` vkládá klientský JavaScript, který odesílá anonymizovaná data o page views přímo do Vercel Analytics dashboardu projektu. Nevyžaduje cookies ani souhlas (dle dokumentace Vercel Analytics jsou data anonymizovaná).

## Implementace

`<Analytics />` komponenta je vložena v `src/app/layout.tsx` (root layout), takže se načítá na každé stránce aplikace.

## Rozhodnutí o knihovně

Viz [ADR 007](../decisions/007-vercel-web-analytics.md).
