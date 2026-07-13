# CoAppraiser evaluations

The eval suite uses synthetic assignment material and does not require customers or real appraisal files.

## Run deterministic workflow tests

```powershell
python manage.py test evals apps.ai_tools
```

These tests cover a synthetic customer journey, workfile persistence, CSV processing, and assignment ownership.

## Run fixture and safety evals

Use the mock provider for repeatable, no-cost output:

```powershell
$env:COAPPRAISER_LLM_PROVIDER = "mock"
$env:COAPPRAISER_LLM_MODEL = "mock-revision-response"
python evals/run.py
```

The runner checks required output fields, verification guidance, required concepts, and prohibited claims. Run a separate live-model pass with `COAPPRAISER_LLM_PROVIDER=openai` only when API spend is intended; compare results to the same rubric and retain the JSON output for regression review.

## Admin insight dashboard

Staff users can open `/admin/dashboard/` for a lightweight operational view of registered users, assignments, source documents, AI actions, saved artifacts, subscriptions, open verification items, and recent model actions. The page is staff-only; detailed object management remains in `/admin/`.
