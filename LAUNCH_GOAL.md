# CoAppraiser Launch Finish-Line Goal

## Objective

Put CoAppraiser over the launch finish line as a coherent, production-ready product:

1. Public marketing copy accurately matches the solutions that are actually live.
2. All public solution pages, navigation, CTAs, signup, pricing, and early-access routes work on mobile and desktop.
3. A visitor can subscribe through the website using Stripe Checkout.
4. Stripe webhooks create and maintain the user's subscription state safely.
5. A subscribed user can access the paid product and manage billing through the Stripe customer portal.
6. The application is deployed and verified on Railway with PostgreSQL.

## Product message to preserve

CoAppraiser is a compliance-first AI copilot for residential appraisers. It helps users prepare revision responses, organize market evidence, review potential UAD 3.6 issues, and keep traceable workfile artifacts alongside their existing appraisal software.

Never imply that CoAppraiser determines value, selects final comparables, makes final adjustments, signs reports, replaces appraisal software, provides official UAD validation, or guarantees USPAP, GSE, lender, AMC, FHA, or VA acceptance.

## Launch scope

### 1. Marketing and positioning alignment

- Audit the homepage, pricing page, early-access page, UAD checklist, skill library, and every solution page against the live application.
- Make the primary message consistent: UAD 3.6 readiness, revision response, market evidence support, and workfile documentation.
- Ensure each solution page describes a workflow that exists in the app or is explicitly labeled as planned.
- Remove stale, generic, exaggerated, or unsupported AI claims.
- Make CTAs intentional and consistent:
  - Subscribe / Start using CoAppraiser for paid plans.
  - Sign in for existing users.
  - View the UAD checklist for visitors who are not ready to subscribe.
  - Contact/early access only where a product workflow is not yet available.
- Preserve SEO titles, descriptions, canonical URLs, structured data, and stable public paths.
- Verify every public link, form, CTA, and navigation item returns the expected page.

### 2. Live solution experience

The following solution routes must be live, linked, and honest:

- Revision Response Agent
- Workfile Guardian
- UAD 3.6 Readiness Review / Issue Explainer
- Market Evidence Pack
- Skill Library
- UAD 3.6 Readiness Checklist

For every live solution:

- Show the user problem, inputs, outputs, boundaries, and next action.
- Link visitors into signup, login, or subscription at the correct point.
- Show the correct compliance disclaimer.
- Avoid fake testimonials, customer counts, lender logos, certifications, or approval claims.
- Test the page on desktop and mobile.

### 3. Stripe subscription system

Use Stripe Checkout and Stripe Billing with Stripe Price IDs supplied through environment variables.

Required implementation:

- Define the initial paid plans in one place and match the public pricing page to those plans.
- Add a billing/subscription model tied to the Django user and Stripe customer/subscription identifiers.
- Add a subscribe endpoint that creates a Stripe Checkout Session server-side.
- Never expose secret keys or trust client-provided prices.
- Add success and cancel routes that return the user to a clear next step.
- Add a Stripe webhook endpoint with signature verification.
- Handle checkout completion, subscription creation/update, cancellation, payment failure, and invoice events needed for access state.
- Make webhook processing idempotent using Stripe event IDs.
- Store subscription status, plan/price, current period dates, cancel-at-period-end, and Stripe IDs.
- Add a billing page showing current status and a link to the Stripe customer portal.
- Add a portal endpoint that creates a portal session server-side for the authenticated user's Stripe customer.
- Do not store card numbers or sensitive payment details in the application database.
- Keep development usable with Stripe test mode and a clearly documented mock/no-billing mode when Stripe is not configured.

### 4. Website subscribe flow

The complete visitor path must work:

1. Visitor reads a solution or pricing page.
2. Visitor chooses a plan.
3. Visitor signs up or signs in.
4. Website creates a Stripe Checkout Session for the selected server-configured price.
5. Visitor completes Stripe Checkout in test mode and returns to CoAppraiser.
6. Webhook confirms the subscription and updates local access state.
7. User sees the active plan and can enter the application.
8. User can open billing settings and manage the subscription in Stripe's portal.
9. Cancellation or failed payment changes access state predictably and displays a useful message.

Access control must be explicit. The app should distinguish at least:

- authenticated but unsubscribed
- active/trialing subscriber
- past-due or unpaid subscriber
- canceled/expired subscriber

Do not lock the user out of account or billing pages merely because payment state changed; provide a clear recovery path.

### 5. Production deployment

- Configure Railway web service and PostgreSQL through `DATABASE_URL`.
- Configure production `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, static files, media strategy, LLM provider, and Stripe variables.
- Use Gunicorn and WhiteNoise.
- Run migrations and static collection as part of the documented release process.
- Configure the production Stripe webhook URL and verify the signing secret.
- Document test-mode and live-mode Stripe setup separately.
- Do not claim production billing is ready until a real Stripe test-mode checkout, webhook, subscription state update, portal session, and cancellation path have all been verified.

## Required tests and evidence

- Marketing route and CTA smoke tests.
- Pricing plan-to-Stripe-price mapping tests.
- Unauthenticated subscribe redirect behavior.
- Authenticated Checkout Session creation with server-side price selection.
- Invalid or tampered price selection rejection.
- Stripe webhook signature rejection for invalid requests.
- Idempotent webhook processing.
- Subscription create/update/cancel state transitions.
- Customer portal access ownership checks.
- Paid feature access checks for each subscription state.
- Existing MVP tests remain green.
- Live local smoke test with Stripe test mode or Stripe CLI webhook forwarding.
- Railway production smoke test after deployment.

## Definition of done

Do not declare this goal complete until:

- Public copy matches live solutions and all public routes/CTAs are verified.
- Pricing plans and Stripe Price IDs are configured without hardcoded secrets.
- A new visitor can sign up, choose a plan, complete Stripe test checkout, and return successfully.
- The webhook updates the local subscription record exactly once per Stripe event.
- The subscribed user can access the intended product and manage billing.
- Cancellation and failed payment states are visible and recoverable.
- Existing users can sign in and use the original MVP workflow.
- Railway deployment, migrations, static files, environment variables, and webhook configuration are documented.
- Automated tests and end-to-end smoke checks pass.
- All compliance and professional-judgment boundaries remain accurate in the UI and marketing copy.

## External launch gate

The repository is prepared for the final external step, but deployment must target a CoAppraiser Railway project rather than the currently selected unrelated Railway project. The operator must provide or select that project and configure Stripe test/live keys and Price IDs before running the hosted checkout, webhook, portal, and cancellation smoke tests.
