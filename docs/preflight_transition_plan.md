# Preflight transition plan

## Audit snapshot

CoAppraiser is a Django modular monolith using PostgreSQL or SQLite, Django auth/forms/templates, HTMX, Tailwind-like existing CSS, WhiteNoise, local media storage, and a simple mock/LLM service. Existing apps are `accounts`, `assignments`, `ai_tools`, `workfile`, `marketing`, and `billing`. The existing product creates assignments, uploads `Document` records, logs AI actions, saves `OutputArtifact` records, tracks verification items, and supports Stripe/mock billing.

## Product transition

The new visible workflow is `Preflight` at `/app/preflight/`. Existing assignment, revision response, market evidence, UAD explainer, workfile, and billing routes remain available as legacy/internal capabilities while customer navigation points to Preflight. Their reusable capabilities are ingestion helpers, AI logs, workfile artifacts, verification patterns, CSV/PDF parsing, and billing authorization.

No existing data is deleted. Legacy records remain in their current tables and are not backfilled with invented provenance. New reviews use the `preflight` app and can later link to legacy records through an explicit migration if needed.

## Implemented domain and migration path

`PreflightReview` owns a customer review; `ReviewVersion` preserves each immutable upload; `ReviewFile` stores classified, hashed source files; `ReviewFinding` stores prioritized observations; `FindingDecision` records user decisions; and `WorkfileReviewRecord` stores an immutable JSON snapshot. The safe migration is additive (`preflight.0001_initial`) and does not alter existing tables.

## Current implementation phases

1. Domain, permissions, upload form, ZIP safety, and XML/PDF/image classification.
2. Deterministic intake findings and finding decisions.
3. Revised package upload, stable finding signatures, and workfile JSON export.
4. Follow-up: richer XML/PDF normalization, rule seeding, AI consistency operations, comparison UI, retention/deletion controls, and background processing using the existing deployment conventions.

## Risks

Uploaded appraisal data is confidential. Production must use private object storage, signed downloads, retention/deletion controls, malware scanning, access logging, and a clear no-training policy. The current initial pass never exposes files publicly and scopes reviews by authenticated user. Preflight is not official GSE validation and must not be marketed as a guarantee.
