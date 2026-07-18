# Build Week public demo

The public judge route is `/demo/`. It requires no account, password, upload, or payment information. The normal customer upload route remains `/app/preflight/new/` and requires authentication.

## Scenarios

| Public title | Fixture | Deterministic outcome | Likely GPT-5.6 categories |
| --- | --- | --- | --- |
| Consistent Package Baseline | `demo/coappraiser-demo-01-ready.zip` | One advisory baseline finding. XML, PDF, narrative, and exhibits align. | Cleanup or advisory review. |
| Conflicting Condition and Commentary | `demo/coappraiser-demo-02-reconcile.zip` | Four warnings: XML/PDF condition, structured/narrative condition, structured/narrative quality, and incomplete comparable commentary. | Fix before delivery and appraiser judgment review. |
| Missing Structured Report Export | `demo/coappraiser-demo-03-incomplete.zip` | One critical missing-XML finding. | Fix before delivery and missing-information review. |

Every file is generated synthetic data. The packages contain no borrower, client, lender, appraiser, signature, credential, or real-property information. GPT-5.6 wording, prioritization, and additional interpretive findings may vary. The deterministic outcomes are regression-tested and predictable.

## Real pipeline

Selecting a scenario creates a fresh `PreflightReview` and `ReviewVersion`. The selected repository ZIP is wrapped as a normal Django upload and passed to the existing `ingest_files()` and `run_deterministic_review()` services. That path performs ZIP safety checks, private file persistence, XML/PDF extraction, deterministic rules, structured GPT review, finding and decision persistence, and workfile generation. Findings are never pre-rendered or hard-coded into the demo.

## Anonymous isolation and cleanup

The first run in a browser session creates a Django user whose username starts with `__coappraiser_demo__` and whose password is unusable. Its database ID and creation time are stored in the signed Django session. Demo detail, decision, workfile, and synthetic-file endpoints require both the review ID and that session owner. A second browser session receives `404` for another session's records.

The demo does not authenticate that generated owner into normal customer routes. Custom uploads therefore continue to require login and normal billing behavior. Stored files are returned only through session-checked Django views; R2 object URLs are not exposed directly.

Demo users expire after `COAPPRAISER_DEMO_RETENTION_HOURS` (default `24`). Visiting the landing page prunes a small expired batch. Production should also run this command at least daily:

```text
python manage.py cleanup_demo_reviews
```

The command removes stored files before deleting expired reviews and generated users.

A one-use launch token prevents double-click or replay from creating duplicate reviews. A processing claim prevents the same review from running twice. Runs stuck longer than `COAPPRAISER_DEMO_STALE_PROCESSING_SECONDS` (default `120`) become retryable failures.

## Production configuration

```text
SECRET_KEY=<strong stable secret>
DEBUG=False
ALLOWED_HOSTS=<deployment host>
CSRF_TRUSTED_ORIGINS=https://<deployment host>
DATABASE_URL=<PostgreSQL URL>
COAPPRAISER_LLM_PROVIDER=openai
COAPPRAISER_LLM_MODEL=gpt-5.6
OPENAI_API_KEY=<secret>
COAPPRAISER_OPENAI_TIMEOUT_SECONDS=60
COAPPRAISER_STORAGE_BACKEND=r2
R2_ACCOUNT_ID=<secret>
R2_BUCKET_NAME=<private bucket>
R2_ACCESS_KEY_ID=<secret>
R2_SECRET_ACCESS_KEY=<secret>
COAPPRAISER_DEMO_RETENTION_HOURS=24
COAPPRAISER_DEMO_STALE_PROCESSING_SECONDS=120
```

`R2_ENDPOINT_URL` is optional because it is derived from `R2_ACCOUNT_ID`. A successful result must show provider `openai`, model `gpt-5.6`, and execution status `Completed`. If the model fails, the page preserves the review, discloses the failure, and never substitutes mock or canned findings.

## Exact judge test

1. Open `/demo/` in a private browser.
2. Choose **Conflicting Condition and Commentary**.
3. Select **Run this Preflight** and wait for the staged processing page.
4. Confirm the summary shows files, deterministic findings, GPT-5.6 findings, highest severity, and completion state.
5. Inspect the first finding's observed conflict, evidence locations, reason, and recommended review action.
6. Compare deterministic checks with the separate GPT-5.6 judgment-review section.
7. Mark one finding **Resolved**, one **Deferred**, and one **Not applicable**; save a short note.
8. Open **View workfile record** and confirm the decisions, timestamps, model, versions, file hashes, and professional-boundary statement.
9. Download the JSON record.
10. Return to `/demo/` and optionally run the clean baseline or missing-XML scenario.

## Verification

```text
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

The automated suite does not make live OpenAI calls. Production model access and end-to-end R2 behavior must be smoke-tested on Railway before submission.
