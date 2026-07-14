# CoAppraiser Demo Media Kit Plan

## Objective

Create a repeatable set of screen recordings that shows the real product experience using synthetic assignment material. No customer data, real property data, real MLS exports, or live payment information should appear in the recordings.

## Demo environment

Seed the environment with the management command:

```powershell
$env:COAPPRAISER_DEMO_PASSWORD = "use-a-local-or-secret-demo-password"
python manage.py seed_demo_data --reset
```

For Railway, set `COAPPRAISER_DEMO_PASSWORD` as a protected service variable and run the command through a one-off Railway shell. Never place the password in Git, a video, or a public document.

The command creates a non-staff account named `demo@coappraiser.com`, an active demo Pro subscription, and four synthetic assignments:

- Demo · GLA revision response
- Demo · Market evidence review
- Demo · UAD 3.6 issue review
- Demo · Workfile Guardian

## Recording goals

### Goal 1 — Product overview

Show the homepage, the four workflows, the signup CTA, and the pricing page. Record a 60–90 second overview explaining who CoAppraiser is for and what it does.

### Goal 2 — Account and assignment setup

Record sign-in with the demo account, the dashboard, an assignment detail page, source material, and the Workfile link. Show that the product begins with an assignment rather than an isolated chat.

### Goal 3 — Revision Response Agent

Open the GLA revision assignment, paste the synthetic reviewer request, generate the response package, edit the draft, and show the verification items and saved artifact.

### Goal 4 — Market Evidence Pack

Open the market assignment, upload or select the synthetic MLS CSV, show column detection and descriptive observations, then show the caution language and workfile memo.

### Goal 5 — UAD 3.6 Readiness Review

Open the UAD assignment, paste the synthetic issue text, generate the explanation, and show the review steps and explicit “not official validation” boundary.

### Goal 6 — Workfile Guardian

Open the workfile assignment and show source documents, AI actions, saved artifacts, and verification items. Mark one item verified and show the state change.

### Goal 7 — Plans and conversion

Record the pricing page, plan comparison, create-account CTA, plan confirmation screen, and Stripe test checkout redirect. Do not enter live card data.

## Playwright recording conventions

- Use a fixed 1440×1000 viewport for desktop recordings.
- Use a separate 390×844 viewport for mobile recordings.
- Start each recording from a known URL and fresh browser context.
- Use synthetic text only.
- Mask or omit account passwords from all captures.
- Wait for visible headings before each screenshot or clip.
- Use stable selectors based on headings, labels, and button text.
- Capture both a clean final frame and the full interaction video.
- Keep each clip focused on one benefit and one workflow.

## Proposed media deliverables

- `01-product-overview.mp4`
- `02-account-and-assignment.mp4`
- `03-revision-response-agent.mp4`
- `04-market-evidence-pack.mp4`
- `05-uad-readiness-review.mp4`
- `06-workfile-guardian.mp4`
- `07-plans-and-checkout.mp4`
- Thumbnail stills for each clip
- Caption/transcript `.vtt` files
- Short clips for homepage and social posts

## Editorial guardrails

Every video should say or visibly communicate:

- Outputs are drafts and require appraiser review.
- The appraiser retains professional judgment.
- CoAppraiser does not determine value or final adjustments.
- UAD support is readiness/issue explanation, not official validation.
- No workflow guarantees USPAP, GSE, lender, AMC, or client acceptance.

## Suggested build order

1. Seed and verify the demo account locally.
2. Record the product overview and account setup.
3. Record the Revision Response Agent, since it is the flagship workflow.
4. Record Workfile Guardian and Market Evidence Pack.
5. Record UAD Readiness and plans/checkout.
6. Add captions, thumbnails, short clips, and website embeds.
