# CoAppraiser Preflight

CoAppraiser Preflight uses GPT-5.6 to review the evidence inside a residential appraisal package, surface traceable inconsistencies before delivery, and preserve the appraiser's decisions in an auditable workfile record. It is a focused, human-in-the-loop pre-delivery review that works alongside existing appraisal software; it does not determine value or replace professional judgment.

## The problem

A completed appraisal can repeat the same fact across XML fields, rendered report language, comparable commentary, and exhibits. Small conflicts or unsupported explanations can become revision requests after delivery. Preflight gives the appraiser one evidence-linked review queue before delivery, then records how each item was resolved, deferred, or found not applicable.

## Why GPT-5.6

Deterministic rules are best for known package and field checks. GPT-5.6 adds the reasoning needed to compare less uniform commentary and extracted evidence while still returning a strict finding schema. CoAppraiser limits the model to supplied evidence and stores the model, prompt version, input snapshot, response, and resulting findings. The production model alias is `gpt-5.6`; see the [official model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol).

## How Codex was used

Codex was used as the repository-level engineering partner: it audited the existing Django workflow, traced upload-to-workfile persistence, hardened the OpenAI request path, created the sanitized demo fixture, added regression tests, and ran the production-readiness checks. Keep Build Week session evidence with the submission materials.

## Build Week scope

CoAppraiser and its initial appraisal workflow existed before Build Week. Work completed during the event focused on the submission concept: production GPT-5.6 configuration, evidence-complete structured findings, separation of deterministic and model findings, resilient error handling, the sanitized and predictable demo package, decision-note/workfile improvements, deployment safety, regression tests, and submission documentation. The repository history and required Codex `/feedback` session ID provide timestamped evidence of that work and the decisions behind it.

## Architecture

- Django, server-rendered templates, HTMX, and PostgreSQL/SQLite.
- `apps/preflight`: private package intake, extraction, versioned findings, decisions, AI execution records, and workfile export.
- `apps/ai_tools/services/llm_client.py`: explicit mock or OpenAI provider with structured JSON output. GPT-5 requests omit unsupported temperature overrides.
- XML and PDF observations retain source locations; deterministic rules and GPT interpretations are stored and displayed separately.
- Cloudflare R2 is required for production uploads. Downloads are authenticated and user-scoped; files are not served from public static paths.
- Railway runs migrations, WhiteNoise static assets, and Gunicorn.

## Human-in-the-loop boundaries

Every finding says that appraiser judgment is required. CoAppraiser may point to supplied evidence and suggest what to review. It must not determine value, select final comparables, recommend a final adjustment, declare USPAP compliance, perform official UAD validation, or guarantee lender, AMC, FHA, VA, Fannie Mae, Freddie Mac, or other GSE acceptance. The appraiser makes and records every decision.

## Local setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:DEBUG = "True"
$env:COAPPRAISER_LLM_PROVIDER = "mock"
$env:COAPPRAISER_LLM_MODEL = "gpt-5.6"
$env:COAPPRAISER_STORAGE_BACKEND = "local"
$env:COAPPRAISER_BILLING_MODE = "mock"
python manage.py migrate
python manage.py runserver
```

Mock mode is explicit and is accepted only for local development and tests. To exercise the live API locally, set `COAPPRAISER_LLM_PROVIDER=openai` and `OPENAI_API_KEY`; a missing key raises a visible failure and never falls back to mock.

## Production environment

Required on Railway:

```text
SECRET_KEY=<strong random value>
DEBUG=False
ALLOWED_HOSTS=<deployment host>
CSRF_TRUSTED_ORIGINS=https://<deployment host>
DATABASE_URL=<Railway PostgreSQL URL>
COAPPRAISER_LLM_PROVIDER=openai
COAPPRAISER_LLM_MODEL=gpt-5.6
OPENAI_API_KEY=<secret>
COAPPRAISER_STORAGE_BACKEND=r2
R2_ACCOUNT_ID=<secret>
R2_BUCKET_NAME=<private bucket>
R2_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<secret>
R2_SECRET_ACCESS_KEY=<secret>
```

Set `COAPPRAISER_BILLING_MODE` and the Stripe variables only if billing is enabled for the deployment. Production mock AI and production local-media uploads are rejected by the application.

## Exact Build Week demo

1. Create a fresh account and open **Preflight**.
2. Choose **New review** and name it `Build Week synthetic review`.
3. Upload [`demo/coappraiser-build-week-demo.zip`](demo/coappraiser-build-week-demo.zip).
4. Run the review. The deterministic section reliably flags condition conflicts, a quality/commentary conflict, and incomplete comparable commentary. GPT findings appear in a separate section.
5. Expand the evidence trail in each finding and compare it with **Extracted evidence**.
6. Mark findings **Resolved**, **Deferred**, or **Not applicable**, add a short decision note, and save each decision.
7. Select **Download workfile record** and show the JSON evidence, model metadata, decisions, notes, limitations, and file hashes.

The package is entirely synthetic. Its auditable source files and expected findings are documented in [`demo/README.md`](demo/README.md).

## Tests

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

The Preflight suite also covers the controlled demo result, user scoping, ZIP safety, evidence-rich conflicts, preserved state after AI failure, decision notes, workfile export, production mock rejection, and GPT-5 structured request parameters.

## Known limitations

- This is readiness support, not official UAD, GSE, lender, or USPAP validation.
- PDF review depends on extractable text; OCR and visual image analysis are not implemented.
- The initial rule set covers a small, explicit subset of appraisal fields and package checks.
- Reviews run synchronously and are intended for modest package sizes.
- Production requires private R2 storage and operational privacy/retention controls.
- GPT findings can vary; the demo's core findings are deterministic so the video remains repeatable.

## Short demo script

> "Appraisal evidence repeats across structured XML, report commentary, and exhibits, so small inconsistencies can survive until delivery. I will upload a fully synthetic package to CoAppraiser Preflight. The app runs versioned deterministic checks and asks GPT-5.6 for a separate evidence-grounded consistency review. Each finding shows what was observed, the exact source location, supporting evidence, why it matters, and what the appraiser should review. The model never determines value or compliance. I can resolve, defer, or mark an item not applicable, record my reasoning, and download an auditable workfile record containing the evidence, model metadata, decisions, and file hashes."

For Devpost, record this as a public YouTube video under three minutes. The audio must explain what was built, how Codex was used, and how GPT-5.6 was used.
