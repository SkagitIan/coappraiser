# Build status

## Completed

- Added a Django project foundation around the existing CoAppraiser frontend identity.
- Added authentication routes, signup, login, and user-scoped assignments.
- Added Assignment, Document, AIActionLog, OutputArtifact, and VerificationItem models and migrations.
- Added the Revision Response Agent using a version-controlled `skills/revision-response/SKILL.md`.
- Added development mock AI output so the workflow works without an API key.
- Added HTMX generation, artifact persistence, approval, and Workfile Guardian history/print view.
- Added Railway-oriented settings, Procfile, environment example, WhiteNoise, and PostgreSQL URL support.
- Wired the existing static marketing routes into Django, including pricing, early access, solution pages, checklist, and skill library.
- Added UAD 3.6 Issue Explainer and Market Evidence Pack workflows, including CSV column detection, descriptive statistics, artifacts, and verification items.
- Added PDF/TXT extraction on authenticated document upload and verification status controls in the workfile.
- Added automated coverage for signup/login, ownership, public routes, skill loading, mock AI persistence, artifact editing/approval, UAD output, CSV analysis, and workfile access.
- Added Stripe-ready Starter, Pro, and Elite plan catalog, subscription state, idempotent webhook records, Checkout, success/cancel pages, customer portal, mock billing mode, and subscription-based workflow access.
- Replaced public pricing/solution CTAs with a real website plan-selection flow and aligned the source marketing copy with the live workflows.
- Verified Django checks, migrations, static collection, dependency imports, live HTTP routes, and the complete test suite.

## Current limitations

- Marketing subpages remain static HTML responses backed by the original files; richer Django-native content editing is not needed for the current public site.
- CSV analysis is intentionally descriptive and does not calculate or recommend a final adjustment.
- Production object storage, teams, OCR, and official UAD integrations remain out of MVP scope.
- Live Stripe account configuration and CoAppraiser Railway deployment still require external credentials and a project target. The available Railway CLI is currently attached to an unrelated `OpenSkagit Railway` project; local Stripe-compatible mock mode and test coverage are available.

## Next milestone

Configure Stripe test/live Price IDs and webhook secret in Railway, deploy, and run the hosted checkout/webhook/portal smoke test.
