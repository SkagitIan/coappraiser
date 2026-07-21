# CoAppraiser Preflight

A pre-delivery evidence-review system for residential appraisers. Preflight opens an appraisal package, checks whether the XML, the rendered report, the commentary, and the selected photos agree with each other, and turns supported inconsistencies into a short action queue. The appraiser reviews the cited evidence, records a decision, and exports an auditable workfile record.

Residential appraisers rely on software that validates whether required fields are complete and properly formatted, but those systems often cannot determine whether the XML, report narrative, photographs, exhibits, and supporting data tell one consistent story.

As appraisal reporting becomes more structured under UAD 3.6, the number of cross-document relationships that must remain accurate and supportable increases. Inconsistencies discovered after delivery can trigger revision requests, underwriting delays, added liability, and uncompensated work.

Appraisers need a final pre-delivery review layer that can identify evidence conflicts across the complete appraisal package, show exactly where those conflicts occur, and preserve the appraiser’s resolution in the workfile—without replacing professional judgment.

## How it Works

1. Intake — the appraiser uploads a ZIP, PDF, XML file, image set, or supported combination.
2. Extraction — Django/Python inventories and hashes the files, extracts supported XML fields and available PDF text, and runs repeatable package checks.
3. Agent review — the Preflight agent reviews the supplied report evidence across text and selected visual sources.
4. Validation — application code validates and filters the agent response before any finding is saved.
5. Decision — the appraiser resolves, defers, marks not applicable, or keeps each item open, and can attach a note to the workfile.

Deterministic checks and agent findings are stored separately. Exact omissions and field mismatches stay predictable and rule-based; the model is reserved for bounded cross-document relationships that fixed rules cannot describe well.
## How we used Codex.

Codex helped reposition the product around one clear workflow: upload a completed appraisal package, cross-check its evidence before delivery, resolve prioritized findings, and preserve the appraiser’s decisions in the workfile.

We then hardened the Django foundation together. Codex improved ZIP and file intake, user-scoped access, private R2 storage, deployment behavior, static assets, authentication screens, and failure handling so uploaded packages would remain intact even when an AI review failed.

With that foundation stable, Codex helped build deterministic package checks for missing exports, conflicting XML and PDF fields, condition and quality inconsistencies, and incomplete comparable commentary. These repeatable checks became the first layer of every review.

Codex then replaced the earlier model integration with the OpenAI Responses API and configured GPT-5.6 as the production reasoning layer. It added strict structured outputs, supported reasoning parameters, request timeouts, retry behavior, and explicit prevention of production mock-AI fallback.

We expanded Preflight into a multimodal workflow. Codex implemented controlled review of normalized XML evidence, extracted PDF text, a selected rendered report PDF, and prioritized appraisal photographs in one evidence package.

Codex added safeguards around the model rather than trusting its response directly. These included confidence thresholds, source-filename verification, duplicate suppression, professional-boundary filters, and rejection of findings that attempted to determine value, recommend adjustments, declare USPAP compliance, or guarantee acceptance.

To make the AI work traceable, Codex added review coverage records showing which files, PDF pages, and photographs were supplied to the Preflight agent, along with model metadata, response duration, accepted findings, and suppressed findings.

Because confidential appraisal files could not be used for a public demonstration, Codex helped create three controlled appraisal packages using synthetic report data and sanitized owner-supplied photographs. The packages represent an aligned review, a package requiring reconciliation, and an incomplete package.

Codex then built a reproducible evaluation system around paired Fannie Mae Appendix D-1 PDF/XML scenarios. We added corpus inventory, field normalization checks, controlled mutations, regression scoring, isolated live GPT-5.6 tests, telemetry, and a documented evaluation protocol.

Once the review engine was measurable, Codex helped redesign the product around the evidence it produced. We added streamed progress messages, review-coverage summaries, prioritized action queues, exact citations, decision controls, real-time decision notes, version history, and downloadable workfile records.

We worked through the public experience section by section. Codex aligned the homepage, signup, login, FAQ, terms, demo, dashboard, and authenticated results pages around the same Preflight message while improving desktop and mobile layouts.

Near submission, I used Codex to remove retired workflows and stale documentation, scan the repository for secrets and private data, verify production settings, test the live judge path, review the Devpost requirements, and confirm that the video and repository met the submission rules.

This was a continuous collaboration recorded across 73 commits after the Submission Period opened. I supplied the appraisal expertise, professional requirements, product decisions, and feedback. Codex translated that direction into implementation, tests, evaluation tooling, documentation, and a working submission-ready product.

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
