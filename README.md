# CoAppraiser

CoAppraiser is a compliance-first AI copilot for residential appraisers. It helps prepare revision-response drafts and traceable workfile artifacts without determining value or replacing professional judgment.

## Local setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

With `COAPPRAISER_LLM_PROVIDER=mock` and `DEBUG=True`, the complete first workflow runs without an API subscription. Set `DATABASE_URL` to Railway PostgreSQL in production. Run `python manage.py collectstatic --noinput` before deployment; Railway uses `web: gunicorn config.wsgi:application`.

## First workflow

Create an account, create an assignment, open Revision Response Agent, paste a reviewer request, generate the structured response, and open the assignment workfile. Generated output is stored with its input snapshot, skill instructions, artifact, and verification items.

## Project structure

`apps/assignments` owns assignments and sources. `apps/ai_tools` owns skills, deterministic tools, and AI actions. `apps/workfile` owns artifacts and verification. Existing public HTML and shared styling remain in the repository.

Run tests with `python manage.py test`. Run `python manage.py check`, `python manage.py makemigrations --check`, and `python manage.py collectstatic --noinput` before deployment. The existing `assets/styles.css` is retained as the current frontend styling; no frontend build step is required for the server-rendered MVP.

## Railway deployment

1. Create a Railway project with a PostgreSQL service.
2. Deploy this repository as a web service.
3. Set `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, and the LLM provider variables in Railway.
4. Run `python manage.py migrate` and `python manage.py collectstatic --noinput` in the deployment/release setup.
5. Railway uses the repository `Procfile`: `gunicorn config.wsgi:application`.

`railway.json` also documents the Nixpacks build, static collection, migration, Gunicorn start command, and `/` health check.

The MVP defaults to SQLite locally and mock AI mode. Production should use Railway PostgreSQL and a persistent media strategy before confidential document uploads are enabled for real users.

## Stripe billing

Local development defaults to `COAPPRAISER_BILLING_MODE=mock`, which lets an authenticated user exercise plan selection without contacting Stripe. For Stripe test mode, set `COAPPRAISER_BILLING_MODE=stripe`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and the three Stripe Price IDs. Configure the webhook endpoint as `/billing/webhook/` for checkout completion, subscription updates, cancellation, and payment failures. The app stores Stripe IDs and subscription state, never card data. Use `/billing/` for the customer portal.

In Railway, set `STRIPE_PRICE_STARTER`, `STRIPE_PRICE_PRO`, and `STRIPE_PRICE_ELITE` to the Stripe recurring Price IDs that match the public $39, $99, and $149 monthly plans. Use separate test and live values; never commit them to the repository.

For local Stripe webhook testing, install the Stripe CLI, run `stripe login`, then use `stripe listen --forward-to localhost:8000/billing/webhook/` and place the printed signing secret in `STRIPE_WEBHOOK_SECRET`. Run with `COAPPRAISER_BILLING_MODE=stripe` and test-mode keys.

## Current workflows

- Revision Response Agent: reviewer request → structured draft → saved artifact → edit/approve → verification checklist.
- Workfile Guardian: source documents, AI actions, artifacts, approval state, and verification history with browser-print export.
- UAD 3.6 Readiness Review: pasted issue explanation with explicit non-validation disclaimer.
- Market Evidence Pack: CSV column detection and descriptive sale-price/DOM/list-to-sale summaries with cautious report language.

## Boundaries

Outputs are drafts. CoAppraiser does not determine value, make final adjustments, provide official UAD validation, or guarantee USPAP, GSE, lender, AMC, FHA, or VA acceptance. The appraiser must review and verify before use.
