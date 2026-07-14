# ADR 0001: Next.js App Router for the Phase 1 Web Application

- Status: accepted for Phase 0
- Date: 2026-07-14

## Context

Keeper Financial needs indexable public brokerage, recruitment, and approved agent-profile pages alongside authenticated candidate and administration routes. The source of truth prefers one React/TypeScript application with server rendering or pre-rendering and identifies Next.js as the default.

## Decision

Use Next.js App Router with React and strict TypeScript. Public pages use a public route group and metadata. Candidate and administration route groups have server layouts that obtain the Supabase session and ask the FastAPI authorization endpoint for area access before rendering. Shared visual primitives live in `packages/ui`.

FastAPI remains the domain and authorization authority. Next.js does not infer authorization from a token or Supabase identity metadata.

## Consequences

- Public pages can use server rendering, static generation, metadata, sitemap, and robots controls as content matures.
- One web application shares design tokens and accessible primitives across public and portal experiences.
- Protected layouts add an API authorization round trip and require careful no-store behavior.
- Supabase session-cookie behavior must be security-reviewed before production.
- A future switch to a client-only SPA would require a separately approved SEO and pre-rendering decision.

No baseline change was needed; this selects the preferred option already documented in `docs/03_ARCHITECTURE_BASELINE.md`.
