# CoAppraiser Preflight

CoAppraiser Preflight uses GPT-5.6 to review the evidence inside a residential appraisal package, surface traceable inconsistencies before delivery, and preserve the appraiser's decisions in an auditable workfile record. It is a focused, human-in-the-loop pre-delivery review that works alongside existing appraisal software; it does not determine value or replace professional judgment.

## The problem

A completed appraisal can repeat the same fact across XML fields, rendered report language, comparable commentary, and exhibits. Small conflicts or unsupported explanations can become revision requests after delivery. Preflight gives the appraiser one evidence-linked review queue before delivery, then records how each item was resolved, deferred, or found not applicable.

## Why GPT-5.6

Deterministic rules are best for known package and field checks. GPT-5.6 adds the multimodal reasoning needed to compare structured XML, the rendered report, narrative evidence, and selected appraisal photos while still returning a strict finding schema. CoAppraiser uses the Responses API with high-detail visual inputs and configurable reasoning effort, limits the model to supplied evidence, and stores the model, prompt version, source manifest, response, confidence, and resulting findings. The production model alias is `gpt-5.6`; see the [official model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol).

## How Codex was used

Codex was used as the repository-level engineering partner: it audited the existing Django workflow, traced upload-to-workfile persistence, hardened the OpenAI request path, created the sanitized demo fixture, added regression tests, and ran the production-readiness checks. Keep Build Week session evidence with the submission materials.

## Build Week scope

CoAppraiser and its initial appraisal workflow existed before Build Week. Work completed during the event focused on the submission concept: production GPT-5.6 configuration, evidence-complete structured findings, separation of deterministic and model findings, resilient error handling, the sanitized and predictable demo package, decision-note/workfile improvements, deployment safety, regression tests, and submission documentation. The repository history and required Codex `/feedback` session ID provide timestamped evidence of that work and the decisions behind it.

## Architecture

- Django, server-rendered templates, HTMX, and PostgreSQL/SQLite.
- `apps/preflight`: private package intake, extraction, versioned findings, decisions, AI execution records, and workfile export.
- `apps/preflight/llm_client.py`: explicit mock or OpenAI provider with strict structured output. GPT-5.6 multimodal reviews use the Responses API and omit unsupported temperature overrides.
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
COAPPRAISER_OPENAI_TIMEOUT_SECONDS=60
COAPPRAISER_VISUAL_REVIEW_ENABLED=true
COAPPRAISER_VISUAL_MAX_IMAGES=6
COAPPRAISER_REASONING_EFFORT=xhigh
COAPPRAISER_MULTIMODAL_TIMEOUT_SECONDS=180
COAPPRAISER_STORAGE_BACKEND=r2
COAPPRAISER_DEMO_RETENTION_HOURS=24
R2_ACCOUNT_ID=<secret>
R2_BUCKET_NAME=<private bucket>
R2_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<secret>
R2_SECRET_ACCESS_KEY=<secret>
```

Set `COAPPRAISER_BILLING_MODE` and the Stripe variables only if billing is enabled for the deployment. Production mock AI and production local-media uploads are rejected by the application.

`xhigh` is the competition-ready reasoning default for the bounded multimodal pass. GPT-5.6 also accepts `max`; use it only after timing a full production package because it can increase latency and cost.

## Exact Build Week demo

1. Open `/demo/` in a fresh private browser. No account or payment information is required.
2. Drag the provided synthetic appraisal ZIP into the Preflight intake area (or tap it on mobile/keyboard).
3. Confirm the package validation message and choose **Run Preflight**.
4. Let the staged page run the real ZIP intake, extraction, deterministic rules, and GPT-5.6 multimodal review.
5. Compare the prioritized rule-based and GPT-5.6 sections, then inspect the exact report/photo sources, confidence, and **Extracted evidence**.
6. Mark findings **Resolved**, **Deferred**, or **Not applicable**, add a short decision note, and save it.
7. Open **View workfile record**, inspect model and evidence metadata, then download the JSON record.

All three packages are entirely synthetic. Their expected findings and the anonymous isolation design are documented in [`docs/build_week_demo.md`](docs/build_week_demo.md).

## Tests

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

The Preflight suite also covers public demo access, replay prevention, anonymous session isolation, all three controlled outcomes, protected customer routes, ZIP safety, preserved state after AI failure, decision notes, workfile export, production mock rejection, and GPT-5 structured request parameters.

## Known limitations

- This is readiness support, not official UAD, GSE, lender, or USPAP validation.
- GPT-5.6 visually reviews one rendered report PDF and a controlled set of supported JPEG, PNG, WebP, or GIF images. Protected PDFs, unsupported formats, poor image quality, and configured size caps can limit that pass; general OCR is not provided.
- The initial rule set covers a small, explicit subset of appraisal fields and package checks.
- Reviews run synchronously and are intended for modest package sizes; the public demo presents truthful stages rather than a fabricated percentage.
- Production requires private R2 storage and operational privacy/retention controls.
- GPT findings can vary; low-confidence items are suppressed and the demo's core findings remain deterministic so the video is repeatable.

## Short demo script

> "Traditional validation checks whether appraisal fields are populated and correctly formatted. CoAppraiser asks whether the entire package tells one consistent story. From this public page I can run a fully synthetic package through the real intake, deterministic checks, and GPT-5.6 evidence review. Each finding shows what was observed, its source and supporting evidence, why the relationship matters, and what the appraiser should review. The appraiser records the decision, and CoAppraiser preserves it in an auditable workfile record."

For Devpost, record this as a public YouTube video under three minutes. The audio must explain what was built, how Codex was used, and how GPT-5.6 was used.
