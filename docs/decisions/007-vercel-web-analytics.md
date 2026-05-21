# ADR 007 — Vercel Web Analytics pro sledování návštěvnosti

**Status:** Accepted  
**Datum:** 2026-05-21

## Context

Chceme základní přehled o využití aplikace (počty návštěv, aktivní uživatelé) bez nutnosti vlastní analytické infrastruktury nebo složité konfigurace.

## Alternativy

1. **Žádná analytika** — nejjednodušší, žádná závislost ani GDPR dopad. Nevýhoda: žádný přehled o utilization.
2. **Google Analytics / Plausible / Matomo** — kompletní analytické platformy. Vyžadují GDPR banner (cookies), vlastní konfiguraci, případně vlastní hosting (Matomo).
3. **Vercel Web Analytics** — integrováno s platformou, anonymizovaná data (bez cookies dle dokumentace Vercel), nulová konfigurace, součástí Vercel plánu.

## Decision

Použit `@vercel/analytics` (`<Analytics />` v root layoutu).

## Důvod

Projekt je nasazen na Vercel; analytics jsou součástí plánu a nevyžadují žádnou další infrastrukturu. Anonymizovaný přístup eliminuje nutnost cookie banneru. Pro proof-of-concept projekt je to proporcionální řešení.
