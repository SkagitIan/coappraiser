# CoAppraiser Preflight

A pre-delivery evidence-review system for residential appraisers. Preflight opens an appraisal package, checks whether the XML, the rendered report, the commentary, and the selected photos agree with each other, and turns supported inconsistencies into a short action queue. The appraiser reviews the cited evidence, records a decision, and exports an auditable workfile record.

Preflight does not determine value and does not replace professional judgment. It surfaces evidence relationships and leaves every decision to the appraiser.

## What it catches

Modern appraisal packages repeat the same property fact across many places: a condition rating appears in the XML, is restated in the PDF, is discussed in an addendum, and is reflected in the photographs. Any one of those can be individually valid while contradicting another.

Field-completeness validation confirms nothing is empty. It cannot tell whether those sources support the same conclusion. Preflight reviews the package as a whole and reports what conflicts, where it was found, the evidence behind it, why it matters, and what to check next.

## Review pipeline

1. Intake — the appraiser uploads a ZIP, PDF, XML file, image set, or supported combination.
2. Extraction — Django inventories and hashes the files, extracts supported XML fields and available PDF text, and runs repeatable package checks.
3. Agent review — the Preflight agent reviews the supplied report evidence across text and selected visual sources.
4. Validation — application code validates and filters the agent response before any finding is saved.
5. Decision — the appraiser resolves, defers, marks not applicable, or keeps each item open, and can attach a note to the workfile.

Deterministic checks and agent findings are stored separately. Exact omissions and field mismatches stay predictable and rule-based; the model is reserved for bounded cross-document relationships that fixed rules cannot describe well.

## Model integration

GPT-5.6 is the reasoning layer inside the Preflight agent. It never receives control of the application and cannot edit an appraisal. Django selects the evidence, calls the model once for a constrained consistency review, validates the result, and decides what is safe to display.

For an eligible package, the request can include:

- normalized XML observations with source paths;
- extracted PDF excerpts;
- the deterministic findings already produced, so the model does not repeat them;
- one selected rendered appraisal PDF; and
- up to six prioritized JPEG, PNG, WebP, or GIF photographs within configured size limits.

The production integration uses the OpenAI Responses API exclusively. The current configuration uses the `gpt-5.6` alias with `xhigh` reasoning effort, high-detail PDF and image inputs, `store=False`, and a strict JSON Schema. The schema requires a concise title, category, severity, observed issue, source location, supporting evidence, significance, recommended review action, confidence, and cited visual filenames for every candidate finding.

Model output is not trusted blindly. Preflight rejects malformed or low-confidence findings, unverified visual filenames, duplicates of the deterministic checks, generic cautions, and responses that cross professional boundaries. Accepted findings are stored with the request snapshot, source manifest, model metadata, duration, structured response, and any suppression reasons. Private chain-of-thought is never requested and never displayed.

The review uses no web search, computer use, external data, autonomous tools, or multiple agents. The model sees only the evidence supplied from the uploaded package.

## Architecture

- **Application:** Django, server-rendered templates, HTMX, and PostgreSQL or SQLite.
- **Review workflow:** `apps/preflight` handles intake, extraction, versions, deterministic checks, agent review, findings, decisions, and workfile records.
- **Model integration:** `apps/preflight/llm_client.py` contains the explicit mock or OpenAI provider and the Responses API request. `apps/preflight/ai_review.py` selects the multimodal evidence and validates candidate findings.
- **Storage:** local storage is limited to development and tests. Production uploads use private Cloudflare R2 objects behind authenticated, user-scoped views.
- **Deployment:** Railway, Gunicorn, WhiteNoise, migrations, and private environment configuration.
- **Audit trail:** file hashes, normalized observations, AI execution records, finding versions, decisions, and downloadable JSON workfile records are persisted.

## Professional boundaries

The appraiser stays in control by design. Preflight must not determine value, choose final comparables, calculate or recommend a final adjustment, declare USPAP compliance, or guarantee acceptance by a lender, AMC, FHA, VA, Fannie Mae, Freddie Mac, or another GSE.

Model-generated guidance is marked in the stored review data as requiring appraiser judgment. The appraiser verifies the source, chooses the outcome, writes any decision note, and remains responsible for the analysis and the final report.

## Demo

Open [`/demo/`](https://coappraiser.com/demo/) in a private browser window. Choose one of the three synthetic appraisal packages, run the intake, and review the result. The demo uses the real package-processing and result interface but replays a captured agent response, giving a predictable, no-cost public experience. No borrower or confidential appraisal data is included.

The three packages demonstrate an aligned package, evidence that needs reconciliation, and an incomplete package. Expected outcomes and sanitization details are documented in [`docs/build_week_demo.md`](docs/build_week_demo.md).

## Run locally

Python 3.12 is recommended. The default development configuration uses SQLite, local file storage, mock billing, and explicit mock AI, so no paid service or API key is needed to exercise the included demo.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DEBUG = "True"
$env:COAPPRAISER_LLM_PROVIDER = "mock"
$env:COAPPRAISER_STORAGE_BACKEND = "local"
$env:COAPPRAISER_BILLING_MODE = "mock"
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/demo/`. The three synthetic packages required for the recorded demo are committed under `demo/`; they contain no borrower or confidential appraisal data. To test a live model review instead, set `COAPPRAISER_LLM_PROVIDER=openai` and provide `OPENAI_API_KEY` in the environment. The application never silently falls back to mock AI when production settings are active.

## Tests

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

The suite covers protected customer data, ZIP safety, deterministic findings, Responses API request parameters, multimodal source limits, invalid model output, professional-boundary suppression, preserved uploads after a model failure, demo session isolation, decisions, and workfile export.

## Evaluation protocol

Official Fannie Mae Appendix D-1 files are intentionally excluded from Git. After downloading the corpus from Fannie Mae, the no-cost evaluation stack can inventory the paired PDF/XML scenarios, validate supported normalization, and run controlled regression mutations:

```powershell
python manage.py import_uad_eval_corpus "C:\path\to\the-downloaded.zip"
python manage.py evaluate_uad_corpus --strict
python manage.py evaluate_uad_regressions --strict
```

Use `scripts/run_evals.ps1` for the combined local gates. Live model cases are opt-in because they incur API cost. The process and recorded results are documented in [`EVAL.md`](EVAL.md) and [`evals/README.md`](evals/README.md).

## Build context

CoAppraiser entered OpenAI Build Week with Django authentication, user-scoped uploads, persisted findings and versions, appraiser decisions, a workfile-record export, private-storage and deployment support, an earlier structured OpenAI integration, tests, and professional boundaries. During the Submission Period, Codex helped extend that foundation into the current Preflight product: an exclusive GPT-5.6 Responses API path; multimodal PDF and photo review with exact source coverage; stricter finding schemas, confidence gates, duplicate suppression, and professional-boundary filters; expanded deterministic cross-source checks; preserved package state when the model fails; streamed progress; a redesigned action queue; a repeatable UAD 3.6 evaluation stack; and the controlled public demo.

Codex worked directly in this repository to inspect the existing code, implement and test those changes, run the evaluation protocol, and tighten the submission experience. Codex is not part of the production review. The deployed application runs deterministic checks and its configured Preflight agent, while the appraiser verifies the evidence and makes every decision. The dated commit history after July 13, 2026, together with the submitted Codex session ID, separates this work from the pre-Build Week foundation.

## License

CoAppraiser is commercial, proprietary software made public for inspection and evaluation. It is **not open-source software**. The repository may be cloned and run for non-commercial evaluation, testing, education, and hackathon judging. Commercial use, redistribution, sublicensing, and publication of modified versions require prior written permission. See [`LICENSE`](LICENSE).
