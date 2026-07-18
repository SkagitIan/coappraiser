# Build Week submission readiness

Use this as the final operator checklist. Do not mark an item complete without checking the deployed build or final submission artifact.

Submission deadline: **Tuesday, July 21, 2026 at 5:00 PM Pacific**. The recommended category is **Work & Productivity**.

## Live deployment

- [ ] Railway deployment is healthy at `/health/` and uses the submitted commit.
- [ ] Migrations and static collection complete without ignored failures.
- [ ] `DEBUG=False`, HTTPS, secure cookies, allowed hosts, and CSRF trusted origins are verified.
- [ ] PostgreSQL and private R2 storage persist across a redeploy.
- [ ] Sign-up, login, logout, authenticated download, and review deletion work in production.

## GPT-5.6 configuration

- [ ] `COAPPRAISER_LLM_PROVIDER=openai`.
- [ ] `COAPPRAISER_LLM_MODEL=gpt-5.6`.
- [ ] `OPENAI_API_KEY` is present and authorized for the model.
- [ ] `COAPPRAISER_VISUAL_REVIEW_ENABLED=true`, and a deployed review records rendered-PDF/photo sources in the AI execution manifest.
- [ ] `COAPPRAISER_REASONING_EFFORT=xhigh` (or deliberately tested `max`), with a sufficient multimodal timeout.
- [ ] A completed production review records provider `openai`, model `gpt-5.6`, and status `completed`.
- [ ] A forced or observed model failure preserves files and deterministic findings, shows a useful message, and never creates a mock result.

## Demo account and data

- [ ] `/demo/` opens in a fresh private browser without registration, credentials, or payment.
- [ ] The featured drag/tap package and both secondary package states create fresh reviews through the real intake pipeline.
- [ ] Separate browser sessions cannot open one another's demo reviews, files, decisions, or workfile records.
- [ ] The demo page and results contain no pricing, Stripe, or retired-workflow prompts.
- [ ] Opening `/demo/` prunes expired demo data, and `python manage.py cleanup_demo_reviews` succeeds as the optional bulk-cleanup command.

## Sanitized demo package

- [ ] `demo/README.md` expected findings match the current rules.
- [ ] XML, PDF, filenames, assignment facts, and conclusions are synthetic; the five owner-supplied reference photos are the approved sanitized set.
- [ ] Approved photos contain no visible address, sign, vehicle, person, or personal portrait and have zero EXIF entries.
- [ ] No borrower, client, lender, appraiser, real address, signature, credential, or confidential assignment data is present.
- [ ] The ZIP hash and final repository copy match the scenario package used in the video.

## Verification

- [ ] `python manage.py check`.
- [ ] `python manage.py makemigrations --check`.
- [ ] `python manage.py test`.
- [ ] `python manage.py collectstatic --noinput`.
- [ ] Secret scan and tracked-file review show no keys, credentials, database files, or private appraisal data.

## Smoke tests

- [ ] Desktop: sign up, upload, findings, evidence, decisions, notes, revised upload, and workfile download.
- [ ] Mobile: navigation, file input, finding cards, decision controls, notes, and download action remain usable.
- [ ] Chrome or Chromium completes the full judge path without console-breaking errors.
- [ ] A second user cannot view or download the first user's review or files.

## Repository and README

- [ ] README production variables and demo path match the deployed configuration.
- [ ] README contains product problem, GPT-5.6 rationale, Codex use, architecture, boundaries, setup, tests, limitations, and demo script.
- [ ] Repository is public with the root `LICENSE` permitting non-commercial judging and testing, or the private repository is shared with `testing@devpost.com` and `build-week-event@openai.com`.
- [ ] Default branch contains the deployed commit, fixture, checklist, migrations, and passing tests.
- [ ] README clearly distinguishes the pre-Build Week baseline from meaningful work completed after July 13, with commit and Codex-session evidence.
- [ ] No conflicting pricing, legacy flagship messaging, broken links, or committed secrets remain in the submission surface.

## Video recording

- [ ] Browser zoom, desktop resolution, and font size make evidence and notes readable.
- [ ] Notifications, password managers, bookmarks, API keys, Railway variables, and personal tabs are hidden.
- [ ] Start at `/demo/`, drag the controlled same-subject ZIP into Preflight, and show the package-validation message before starting the review.
- [ ] Show `rear_deck_exterior.jpg` or `rear_exterior_condition.jpg` and its exact filename on a GPT-5.6 visual finding; do not promise identical wording on every run.
- [ ] Show the sanitized ZIP, prioritized deterministic and GPT sections, source evidence, three decision states, a decision note, and workfile download.
- [ ] State the professional boundaries aloud: no value conclusion, final adjustment, USPAP declaration, or acceptance guarantee.
- [ ] Audio explains what was built, how Codex was used, and how GPT-5.6 was used.
- [ ] Upload to public YouTube, keep the video under three minutes, and use only licensed assets, music, and trademarks.
- [ ] Keep a backup local recording and verify audio before upload.

## Devpost assets and Codex evidence

- [ ] Project state is **Submitted**, not `submission_draft`, before the deadline.
- [ ] Required **Submitter Type** and **Country of Residence** fields are complete.
- [ ] Select exactly one category: **Work & Productivity**.
- [ ] Final title, one-sentence concept, and edited-in-your-own-voice project description match the README.
- [ ] Repository URL, public-demo testing instructions, live URL, demo video, screenshots, thumbnail, and team details are ready.
- [ ] Working test access remains free through judging; put any credentials only in the private testing-instructions field.
- [ ] Screenshots contain only the synthetic package and no secrets or private browser data.
- [ ] Technology list accurately names Django, GPT-5.6, OpenAI structured outputs, PostgreSQL, R2, and Railway.
- [ ] Known limitations and human-in-the-loop boundaries are included where the form permits.
- [ ] Generate and enter the required Codex Session ID using `/feedback`.
- [ ] Preserve timestamped Codex session and commit evidence showing the meaningful Build Week extensions, repository inspection, implementation, and verification.
- [ ] Final submission clearly supports the four judging criteria: technological implementation, coherent design, credible impact, and quality of the idea.
