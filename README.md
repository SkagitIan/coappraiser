# CoAppraiser Preflight

CoAppraiser Preflight is a pre-delivery review system for residential appraisers. It opens an appraisal package, checks whether the XML, rendered report, commentary, and selected photos tell the same story, and turns supported inconsistencies into a short action queue. The appraiser reviews the cited evidence, records a decision, and exports an auditable workfile record. CoAppraiser does not determine value or replace professional judgment.

## The problem

The same property fact can appear in several places inside one appraisal package. A condition rating may be present in XML, repeated in the PDF, discussed in an addendum, and reflected in photographs. Traditional validation can catch an empty field without noticing that those sources disagree.

Preflight gives the appraiser one review before delivery: what conflicts, where it was found, the evidence behind it, why it matters, and what to check next.

## How Preflight works

1. The appraiser uploads a ZIP, PDF, XML file, image set, or supported combination.
2. Django inventories and hashes the files, extracts supported XML fields and available PDF text, and runs repeatable package checks.
3. The Preflight agent reviews the supplied report evidence across text and selected visual sources.
4. Application code validates and filters the agent response before saving any finding.
5. The appraiser resolves, defers, marks not applicable, or keeps each item open and can add a decision note for the workfile.

Deterministic checks and agent findings are stored separately. Exact omissions and field mismatches stay predictable; the model is used for bounded cross-document relationships that fixed rules cannot describe well.

## How GPT-5.6 is used

GPT-5.6 is the reasoning layer inside the Preflight agent. It does not receive control of the application and it cannot edit an appraisal. Django decides which evidence is sent, calls the model once for a constrained consistency review, validates the result, and decides what is safe to display.

For an eligible package, the request can include:

- normalized XML observations with source paths;
- extracted PDF excerpts;
- the deterministic findings already produced, so the model does not repeat them;
- one selected rendered appraisal PDF; and
- up to six prioritized JPEG, PNG, WebP, or GIF photographs within configured size limits.

The production integration uses the OpenAI Responses API exclusively. The current configuration uses the `gpt-5.6` alias with `xhigh` reasoning effort, high-detail PDF and image inputs, `store=False`, and a strict JSON Schema. The schema requires a concise title, category, severity, observed issue, source location, supporting evidence, significance, recommended review action, confidence, and cited visual filenames for every candidate finding.

The model response is not trusted blindly. CoAppraiser rejects malformed or low-confidence findings, unverified visual filenames, duplicates of repeatable checks, generic cautions, and responses that cross professional boundaries. Accepted model findings are stored with the request snapshot, source manifest, model metadata, duration, structured response, and any suppression reasons. Private chain-of-thought is neither requested nor displayed.

GPT-5.6 is useful here because the job requires reasoning across structured data, report language, page content, and photographs while returning application-ready data. The `gpt-5.6` alias currently routes to GPT-5.6 Sol, which supports text and image input, reasoning, and Structured Outputs. See the official [GPT-5.6 model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol) and [file-input guide](https://developers.openai.com/api/docs/guides/file-inputs).

The appraisal review does not use web search, computer use, external data, autonomous tools, or multiple agents. The model reviews only the evidence supplied from the uploaded package.

## How Codex was used

Codex worked directly in this repository as the engineering collaborator. It first inspected the existing Django workflow, then helped turn it into a complete, testable product path rather than generating a separate prototype.

Codex was used to:

- replace mixed model integrations with one Responses API path for text, PDFs, and photographs;
- design and test the strict finding schema and professional-boundary filters;
- preserve uploaded packages and show a useful error when a model call fails;
- build repeatable package checks, visual-source tracking, decision notes, and workfile exports;
- create three sanitized demonstration outcomes and a recorded public demo that does not spend API tokens on every visit;
- build the Fannie Mae Appendix D-1 evaluation workflow without committing third-party files;
- iterate on the server-rendered interface from real screenshots and hands-on demo feedback;
- audit production mock fallback, private storage, secrets, migrations, static assets, and stale product copy; and
- run Django checks, tests, browser flows, and deployment-oriented verification after changes.

Codex is not part of the production appraisal review. The deployed application runs its own deterministic checks and its configured Preflight agent; the appraiser makes every decision.

## Architecture

- **Application:** Django, server-rendered templates, HTMX, and PostgreSQL or SQLite.
- **Review workflow:** `apps/preflight` handles intake, extraction, versions, deterministic checks, agent review, findings, decisions, and workfile records.
- **Model integration:** `apps/preflight/llm_client.py` contains the explicit mock or OpenAI provider and Responses API request. `apps/preflight/ai_review.py` selects multimodal evidence and validates candidate findings.
- **Storage:** local storage is limited to development and tests. Production uploads use private Cloudflare R2 objects behind authenticated, user-scoped views.
- **Deployment:** Railway, Gunicorn, WhiteNoise, migrations, and private environment configuration.
- **Audit trail:** file hashes, normalized observations, AI execution records, finding versions, decisions, and downloadable JSON workfile records are persisted.

## The appraiser stays in control

Preflight surfaces evidence relationships and suggests what to review. It must not determine value, choose final comparables, calculate or recommend a final adjustment, declare USPAP compliance, or guarantee acceptance by a lender, AMC, FHA, VA, Fannie Mae, Freddie Mac, or another GSE.

Model-generated guidance is marked as requiring appraiser judgment in the stored review data. The appraiser verifies the source, chooses the outcome, writes any decision note, and remains responsible for the analysis and final report.

## Demo

Open [`/demo/`](https://coappraiser.com/demo/) in a private browser. Choose one of the three synthetic appraisal packages, run the simulated intake, and review the recorded result. The demo uses the real package-processing and result interface but replays a captured agent response for a predictable, no-cost public experience. No borrower or confidential appraisal data is included.

The three packages demonstrate an aligned package, evidence that needs reconciliation, and an incomplete package. Expected outcomes and sanitization details are documented in [`docs/build_week_demo.md`](docs/build_week_demo.md).

## Tests

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

The test suite covers protected customer data, ZIP safety, deterministic findings, Responses API request parameters, multimodal source limits, invalid model output, professional-boundary suppression, preserved uploads after model failure, demo session isolation, decisions, and workfile export.

## Evaluation protocol

Official Fannie Mae Appendix D-1 files are intentionally excluded from Git. After downloading the corpus from Fannie Mae, the no-cost evaluation stack can inventory the paired PDF/XML scenarios, validate supported normalization, and run controlled regression mutations:

```powershell
python manage.py import_uad_eval_corpus "C:\path\to\the-downloaded.zip"
python manage.py evaluate_uad_corpus --strict
python manage.py evaluate_uad_regressions --strict
```

Use `scripts/run_evals.ps1` for the combined local gates. Live model cases are opt-in because they incur API cost. The process and recorded results are explained in [`EVAL.md`](EVAL.md) and [`evals/README.md`](evals/README.md).

## License

CoAppraiser is commercial, proprietary software made public for inspection and evaluation. It is **not open-source software**. The repository may be cloned and run for non-commercial evaluation, testing, education, and hackathon judging. Commercial use, redistribution, sublicensing, and publication of modified versions require prior written permission. See [`LICENSE`](LICENSE).
