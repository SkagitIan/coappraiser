# CoAppraiser Preflight

CoAppraiser Preflight uses GPT-5.6 to review the evidence inside a residential appraisal package, surface traceable inconsistencies before delivery, and preserve the appraiser's decisions in an auditable workfile record. It is a focused, human-in-the-loop pre-delivery review that works alongside existing appraisal software; it does not determine value or replace professional judgment.

## The problem

A completed appraisal can repeat the same fact across XML fields, rendered report language, comparable commentary, and exhibits. Small conflicts or unsupported explanations can become revision requests after delivery. Preflight gives the appraiser one evidence-linked review queue before delivery, then records how each item was resolved, deferred, or found not applicable.

## Why GPT-5.6

Appraisal review is not a simple extraction or classification task. A useful review may require connecting a structured condition rating to narrative language on another report page and to a visible condition in a photograph, then explaining that relationship without making the appraiser's decision. Deterministic rules remain the better tool for known omissions and exact field mismatches; GPT-5.6 handles the bounded cross-document interpretation that fixed rules cannot express well.

The production alias is `gpt-5.6`, which currently routes to GPT-5.6 Sol, OpenAI's frontier model for complex professional work. We chose it for the submission because it combines text and image input, reasoning controls, PDF file input through the Responses API, and strict Structured Outputs in one model. The model supports a much larger context than CoAppraiser currently sends; the application deliberately limits each review to the relevant evidence rather than filling the context window. See OpenAI's [GPT-5.6 model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/latest-model), and [file-input documentation](https://developers.openai.com/api/docs/guides/file-inputs).

### The Preflight reviewer agent

“Agent” in CoAppraiser means a specialized, bounded reviewer controlled by the Django workflow. It is not an autonomous valuation agent, an Agents SDK deployment, or a multi-agent system. Django performs package intake, source selection, deterministic checks, persistence, permissions, and workfile generation. GPT-5.6 receives one constrained review task and returns candidate findings; it has no browser, external data source, report-writing tool, or ability to alter an appraisal.

The runtime sequence is:

1. Django validates the ZIP, hashes and stores its files, extracts XML fields and available PDF text, and runs deterministic package rules.
2. The application builds a source manifest containing extracted observations, short PDF excerpts, the deterministic findings already produced, one selected rendered report PDF, and—by default—up to six prioritized appraisal photos.
3. GPT-5.6 performs one consistency review through the Responses API at configurable reasoning effort. The same request path and strict finding schema apply whether the package supplies text alone or text plus visual sources.
4. A strict JSON Schema requires every candidate finding to include its title, category, severity, observed issue, source location, evidence, significance, review action, confidence, visual sources, and an appraiser-judgment reminder.
5. Application code validates the response, rejects unverified visual filenames, suppresses low-confidence items and duplicates of deterministic findings, and persists the accepted findings separately from rule-based findings.
6. The appraiser—not the model—resolves, defers, or marks each item not applicable and records the decision in the workfile record.

### GPT-5.6 features used

| GPT-5.6 capability | CoAppraiser implementation | Why it matters here |
| --- | --- | --- |
| Responses API | Uses one production API path for text-only and multimodal reviews, adding the rendered PDF and selected photos when available. | The reviewer gets GPT-5.6's preferred reasoning interface without making visual evidence a requirement for every package. |
| PDF file input | Sends the selected report as a Base64 `input_file` with `detail: high`; the API supplies extracted text and page images to the vision-capable model. | Small print, page layout, labels, and rendered content remain available alongside extracted report text. |
| Image understanding | Sends supported appraisal photos as high-detail `input_image` items, each paired with its exact filename. | A finding can trace a narrow visual observation back to the actual exhibit and compare it with XML or narrative evidence. |
| Reasoning effort | Uses `xhigh` for the competition configuration; `max` is supported as an opt-in production experiment. | Cross-source inconsistencies require more deliberate comparison than ordinary summarization, while the setting remains measurable and configurable. |
| Structured Outputs | Uses a strict JSON Schema with no additional properties and fixed category, severity, and confidence values. | Model output becomes validated application data rather than an unstructured wall of prose. |
| Data-control option | Sets `store=False` on the Responses API request and sends only files selected within configured count and byte limits. | The integration minimizes unnecessary model-side persistence and unnecessary evidence transfer; operators still remain responsible for the applicable OpenAI account and retention settings. |

CoAppraiser does **not** use GPT-5.6's web search, programmatic tool calling, computer use, persisted reasoning, or multi-agent beta during an appraisal review. Those capabilities are powerful, but they would add external state or autonomous action without improving this submission's central promise: a traceable review of the evidence already inside the package. The application stores the model name, prompt, input snapshot, visual-source manifest, final structured response, suppressed-item reasons, and resulting findings. It does not display or store private chain-of-thought.

## How Codex was used

Codex was the repository-level engineering agent used to turn an existing Django prototype into the Build Week submission. Working against the real repository, it:

- inspected the upload-to-workfile path before changing it;
- implemented and tested the GPT-5.6 Responses API, visual-input, reasoning-effort, and Structured Output path;
- hardened production configuration so a failed or missing model request preserves the uploaded package and never silently substitutes mock output;
- created the controlled same-subject demo packages, sanitized photo set, and predictable deterministic findings;
- iterated on the server-rendered interface using screenshots and end-to-end workflow feedback;
- audited secrets, storage defaults, stale product paths, migrations, static assets, and deployment configuration; and
- repeatedly ran the Django checks, full test suite, fresh-database migration, and GitHub Actions workflow.

Codex is a development collaborator, not part of the production appraisal decision path. Runtime findings come from the deployed Preflight rules and configured GPT-5.6 request. Keep the Build Week Codex session evidence with the submission materials.

## Build Week scope

CoAppraiser and its initial appraisal workflow existed before Build Week. Work completed during the event focused on the submission concept: production GPT-5.6 configuration, evidence-complete structured findings, separation of deterministic and model findings, resilient error handling, the sanitized and predictable demo package, decision-note/workfile improvements, deployment safety, regression tests, and submission documentation. The repository history and required Codex `/feedback` session ID provide timestamped evidence of that work and the decisions behind it.

## Architecture

- Django, server-rendered templates, HTMX, and PostgreSQL/SQLite.
- `apps/preflight`: private package intake, extraction, versioned findings, decisions, AI execution records, and workfile export.
- `apps/preflight/llm_client.py`: explicit mock or OpenAI provider with strict structured output. Every production GPT-5.6 review uses the Responses API with configurable reasoning effort and no temperature override.
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
2. Drag the featured controlled appraisal ZIP into the Preflight intake area (or tap it on mobile/keyboard).
3. Confirm the package validation message and choose **Run Preflight**.
4. Let the staged page run the real ZIP intake, extraction, deterministic rules, and GPT-5.6 multimodal review.
5. Compare the prioritized rule-based and GPT-5.6 sections, then inspect the exact report/photo sources, confidence, and **Extracted evidence**.
6. Mark findings **Resolved**, **Deferred**, or **Not applicable**, add a short decision note, and save it.
7. Open **View workfile record**, inspect model and evidence metadata, then download the JSON record.

All assignment facts, identities, locations, comparables, report statements, and conclusions in the three packages are synthetic. The five owner-supplied residential reference photos were selected to exclude addresses, signs, vehicles, people, and personal portraits, then re-encoded without EXIF metadata. Their expected findings and anonymous isolation design are documented in [`docs/build_week_demo.md`](docs/build_week_demo.md).

## Tests

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

The Preflight suite also covers public demo access, replay prevention, anonymous session isolation, all three controlled outcomes, protected customer routes, ZIP safety, preserved state after AI failure, decision notes, workfile export, production mock rejection, and GPT-5 structured request parameters.

### Official-sample evaluation foundation

CoAppraiser keeps third-party evaluation data out of Git. Download **Appendix D-1:
URAR Sample Scenarios and XML Files** from the Fannie Mae UAD Documentation page,
then create a hashed local inventory:

```powershell
python manage.py import_uad_eval_corpus "C:\path\to\the-downloaded.zip"
python manage.py evaluate_uad_corpus --strict
python manage.py evaluate_uad_regressions --strict
```

On Windows, the same no-cost gates can be run with:

```powershell
.\scripts\run_evals.ps1
```

Add `-Full` for Django checks and tests. Add `-Live -Repeat 1` for the three
paid, isolated GPT-5.6 cases; use `-Repeat 3` when collecting release evidence.
The live wrapper imports Railway model credentials but never uses the production
database or production file storage. See [`evals/README.md`](evals/README.md).

The command validates paths and size limits, extracts only supported files beneath
the ignored `.eval-data/` directory, identifies candidate PDF/XML pairs, and
profiles namespace-heavy XML without pretending that unknown tags are supported
facts. See [`evals/README.md`](evals/README.md) for the operator process,
[`EVAL.md`](EVAL.md) for a plain-English explanation of the tests, results,
failures, fixes, and locked release protocol, and
[`PRODUCT_ROADMAP.md`](PRODUCT_ROADMAP.md) for the product-quality roadmap.

## Known limitations

- This is readiness support, not official UAD, GSE, lender, or USPAP validation.
- GPT-5.6 visually reviews one rendered report PDF and a controlled set of supported JPEG, PNG, WebP, or GIF images. Protected PDFs, unsupported formats, poor image quality, and configured size caps can limit that pass; general OCR is not provided.
- The initial rule set covers a small, explicit subset of appraisal fields and package checks.
- Reviews run synchronously and are intended for modest package sizes; the public demo presents truthful stages rather than a fabricated percentage.
- Production requires private R2 storage and operational privacy/retention controls.
- GPT findings can vary; low-confidence items are suppressed and the demo's core findings remain deterministic so the video is repeatable.
- The controlled photos are real owner-supplied residential reference images, not evidence from an appraisal assignment; demo report data must not be treated as describing an actual property.

## Short demo script

> "Traditional validation checks whether appraisal fields are populated and correctly formatted. CoAppraiser asks whether the entire package tells one consistent story. These three controlled packages show the same fictional subject with aligned, conflicting, or incomplete report evidence. GPT-5.6 reads the rendered report and selected residential photos while deterministic rules reconcile exact XML and PDF fields. Each finding shows what was observed, its source and supporting evidence, why it matters, and what the appraiser should review. The appraiser records the decision, and CoAppraiser preserves it in an auditable workfile record."

For Devpost, record this as a public YouTube video under three minutes. The audio must explain what was built, how Codex was used, and how GPT-5.6 was used.

## License

CoAppraiser is source-available for non-commercial evaluation, testing, educational review, and hackathon judging. Commercial use, redistribution, and modified publication require prior written permission. See [`LICENSE`](LICENSE).
