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
- [ ] A completed production review records provider `openai`, model `gpt-5.6`, and status `completed`.
- [ ] A forced or observed model failure preserves files and deterministic findings, shows a useful message, and never creates a mock result.

## Demo account and data

- [ ] A fresh judge flow can create an account without staff access.
- [ ] If using a prepared demo account, credentials are stored only in the private submission notes and rotated afterward.
- [ ] The account can create at least one Preflight review without an unexpected billing block.
- [ ] `demo/coappraiser-build-week-demo.zip` uploads within the production request timeout.

## Sanitized demo package

- [ ] `demo/README.md` expected findings match the current rules.
- [ ] XML, PDF, images, filenames, and metadata contain only synthetic information.
- [ ] No borrower, client, lender, appraiser, real address, signature, credential, or confidential assignment data is present.
- [ ] The ZIP hash and final repository copy are the package used in the video.

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
- [ ] Repository is public with relevant licensing, or the private repository is shared with `testing@devpost.com` and `build-week-event@openai.com`.
- [ ] Default branch contains the deployed commit, fixture, checklist, migrations, and passing tests.
- [ ] README clearly distinguishes the pre-Build Week baseline from meaningful work completed after July 13, with commit and Codex-session evidence.
- [ ] No conflicting pricing, legacy flagship messaging, broken links, or committed secrets remain in the submission surface.

## Video recording

- [ ] Browser zoom, desktop resolution, and font size make evidence and notes readable.
- [ ] Notifications, password managers, bookmarks, API keys, Railway variables, and personal tabs are hidden.
- [ ] Start from account creation or clearly explain the prepared demo account.
- [ ] Show the sanitized ZIP, prioritized deterministic and GPT sections, source evidence, three decision states, a decision note, and workfile download.
- [ ] State the professional boundaries aloud: no value conclusion, final adjustment, USPAP declaration, or acceptance guarantee.
- [ ] Audio explains what was built, how Codex was used, and how GPT-5.6 was used.
- [ ] Upload to public YouTube, keep the video under three minutes, and use only licensed assets, music, and trademarks.
- [ ] Keep a backup local recording and verify audio before upload.

## Devpost assets and Codex evidence

- [ ] Project state is **Submitted**, not `submission_draft`, before the deadline.
- [ ] Select exactly one category: **Work & Productivity**.
- [ ] Final title and one-sentence concept match the README.
- [ ] Short description, long description, repository URL, live URL, demo video, screenshots, thumbnail, and team details are ready.
- [ ] Working test access remains free through judging; put any credentials only in the private testing-instructions field.
- [ ] Screenshots contain only the synthetic package and no secrets or private browser data.
- [ ] Technology list accurately names Django, GPT-5.6, OpenAI structured outputs, PostgreSQL, R2, and Railway.
- [ ] Known limitations and human-in-the-loop boundaries are included where the form permits.
- [ ] Generate and enter the required Codex Session ID using `/feedback`.
- [ ] Preserve timestamped Codex session and commit evidence showing the meaningful Build Week extensions, repository inspection, implementation, and verification.
