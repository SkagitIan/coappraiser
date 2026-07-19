# CoAppraiser execution backlog

This file turns the remaining product work into bounded goals. It is not a
feature wish list. CoAppraiser's near-term job is to make the existing Preflight
workflow dependable, difficult to abuse, measurable, and easy for an independent
residential appraiser to trust.

`PRODUCT_ROADMAP.md` describes the product direction. `EVAL.md` explains the
current evidence and evaluation protocol. This file is the ordered implementation
queue.

## How to use this backlog

- Work in priority order unless a dependency says otherwise.
- Complete one goal in a small, reviewable change.
- A goal is not done until its acceptance criteria, tests, documentation, and
  production verification are complete.
- Do not broaden a product claim until an evaluation supports it.
- Preserve the current professional boundaries: no value determination, final
  adjustment recommendation, comparable selection, USPAP declaration, official
  UAD validation, or guarantee of lender, AMC, or GSE acceptance.
- Keep private appraisal packages, the official Appendix D-1 archive, generated
  evaluation data, credentials, and production data out of Git.

## Priority 0 — close the submission cleanly

### Goal 0.1 — Complete the Build Week submission

**Outcome:** A judge can understand, access, and test the same product shown in
the video without needing private help.

**Why this remains:** The application and evaluation foundation are ready, but
the video, final Devpost form, and Codex session evidence are manual submission
steps.

**Scope:**

- Record a video under three minutes using the controlled demo package.
- Show package intake, live review status, evidence-backed findings, an appraiser
  decision, and the workfile download.
- Enter the live URL, public repository, screenshots, testing instructions,
  technology list, known limitations, and final project description in Devpost.
- Generate and save the required Codex session ID with `/feedback`.
- Correct final submission copy and typographical errors before publishing.

**Done when:**

- Every unchecked manual item in `BUILD_WEEK_SUBMISSION.md` has been verified.
- The video and live site show only synthetic or authorized sanitized material.
- The repository commit in Devpost matches the deployed commit.
- A fresh judge session can complete the demo without credentials or payment.

**Not part of this goal:** New product features or a redesigned submission flow.

### Goal 0.2 — Align the public promise with the verified product

**Outcome:** The homepage, demo, pricing, signup, login, FAQ, Terms, and product
workspace describe one clear promise: peace of mind from an evidence-backed
Preflight review before delivery.

**Why this remains:** The core positioning is strong, but several phrases can
still imply official clearance or complete inspection. The newer GPT-5.6 visual
and PDF capabilities also need to be explained accurately and consistently.

**Scope:**

- Use plain, reassuring language for appraisers who have never used GPT.
- Explain that GPT-5.6 cross-checks the rendered report, normalized XML evidence,
  and a controlled set of package photos.
- Replace claims such as "Ready for Client Delivery," "UAD cleared," or
  "no black-box decisions" with precise language about a cleared Preflight queue,
  supported checks, and no automatic appraisal decisions.
- Add a concise proof section explaining what GPT-5.6 does and how Codex helped
  build and test the system.
- Keep one professional-boundary statement per page instead of repeating caveats.

**Done when:**

- Every public page uses the name `CoAppraiser Preflight` consistently.
- Claims match `README.md`, `EVAL.md`, the actual model inputs, and current evals.
- Pricing consistently says one promotional review, then $59/month.
- Desktop and mobile copy has no overflow, clipped text, duplicated sections, or
  dead links.
- Public-page regression tests cover the most important claims and routes.

**Not part of this goal:** Inventing new capabilities to make the copy stronger.

## Priority 1 — protect revenue and make production dependable

### Goal 1.1 — Replace the free-scan shortcut with a durable entitlement

**Outcome:** Each eligible customer receives exactly one promotional Preflight
review, and deleting a review cannot restore it.

**Why this is urgent:** The current gate checks whether a `PreflightReview` row
exists. A user can delete the review and receive another free scan, and two
simultaneous requests may both pass the check.

**Scope:**

- Store promotional eligibility and consumption in an immutable usage or
  entitlement record separate from appraisal reviews.
- Consume the entitlement atomically when processing is accepted.
- Decide and document whether a failed intake returns the credit; a completed
  model failure must not silently create unlimited retries.
- Keep promotional usage after a review is deleted.
- Allow a staff member to grant or restore a credit with an audited reason.
- Keep the public synthetic demo separate from customer upload entitlements.
- Add conservative account and IP rate limits to signup, login, demo launch, and
  review creation without invasive browser fingerprinting.

**Done when:**

- Deleting the first review does not restore the promotional credit.
- Concurrent create requests cannot spend one credit twice.
- Revised versions of the same review do not consume a new credit.
- Active subscribers can create reviews; past-due, canceled, and unpaid behavior
  is explicitly tested and documented.
- Server-side enforcement cannot be bypassed by changing a form, URL, or request.
- Tests cover success, failed upload, provider failure, deletion, concurrency,
  staff override, and demo isolation.

**Dependencies:** Goal 1.2 for verified-account eligibility.

**Not part of this goal:** Government-ID checks, device fingerprinting, or a
promise that one person can never create multiple accounts. Controls should make
casual abuse uneconomic without collecting unnecessary personal data.

### Goal 1.2 — Add a complete, secure account lifecycle

**Outcome:** A customer can verify, recover, and close an account without staff
intervention, and an unverified address cannot consume the promotional review.

**Why this remains:** Signup currently creates and logs in a user immediately.
There is no implemented email verification policy, and the default Django
password-reset routes are not useful until email delivery and templates are
configured and tested.

**Scope:**

- Require a unique, verified email before a promotional review can run.
- Configure transactional email and complete password-reset templates.
- Add login and signup throttling with useful non-revealing error messages.
- Provide account deletion with a clear explanation of review, file,
  subscription, and backup behavior.
- Define how active Stripe subscriptions are canceled or handed off before
  account deletion.
- Keep usernames as an internal implementation detail if email is the customer's
  actual identity.

**Done when:**

- Verification and password-reset links expire and cannot be reused improperly.
- Duplicate email addresses cannot create duplicate promotional entitlements.
- Account enumeration is not exposed through login, reset, or signup responses.
- Closing an account removes active review data and stored files through the same
  verified deletion path used elsewhere.
- Email, authentication, deletion, and subscription edge cases have automated
  tests and a production smoke test.

**Not part of this goal:** Social login, teams, invitations, or enterprise SSO.

### Goal 1.3 — Move review execution out of the web request

**Outcome:** An uploaded package completes reliably even if the browser closes,
the connection drops, or GPT-5.6 takes longer than a web worker should remain
open.

**Why this is urgent:** The current normal and demo reviews perform the
deterministic and GPT work inside a streaming HTTP request. Production Gunicorn
times out at 120 seconds while the configured multimodal model call can wait 180
seconds.

**Scope:**

- Add a durable background job for normalization, deterministic checks, GPT
  review, completion, and failure handling.
- Persist truthful milestones and let the progress page poll or stream those
  stored events.
- Make job submission and execution idempotent.
- Add bounded retries for transient provider and storage failures.
- Detect and recover jobs left in `processing` after a worker restart.
- Preserve the upload, normalized evidence, deterministic results, model
  execution record, and useful user message on failure.
- Run a separate Railway worker or equivalent process with documented commands.

**Done when:**

- Closing the progress page does not stop the review.
- Refreshing or reposting cannot create duplicate model charges or findings.
- A worker restart and a simulated OpenAI timeout have tested recovery paths.
- Web requests return promptly and no application timeout is shorter than an
  operation it is expected to perform.
- The progress UI remains truthful and never fabricates a percentage.

**Dependencies:** Goal 1.1 so a job and its paid or promotional entitlement are
created in one consistent transaction.

**Not part of this goal:** A new JavaScript framework, autonomous multi-agent
workflow, or real-time token-by-token model prose.

### Goal 1.4 — Notify customers when attention is needed

**Outcome:** A customer does not need to watch a long-running page to know that a
review completed or failed.

**Why this matters:** Background processing removes the need to keep a browser
open, but it also requires a clear return path.

**Scope:**

- Add in-app notifications for completed, failed, and recovered reviews.
- Send transactional email for completion and actionable failure.
- Link to the authenticated review; never include an address, appraisal
  conclusion, finding evidence, report image, or borrower information in email.
- Deduplicate notifications across retries and worker restarts.
- Provide a simple email preference while retaining necessary account and
  security notices.

**Done when:**

- Each terminal review state produces at most one customer notification.
- Notification links enforce the existing user scope.
- Failed email delivery does not fail or rerun the appraisal review.
- Tests cover deduplication, privacy-safe content, preferences, and access control.

**Dependencies:** Goals 1.2 and 1.3.

**Not part of this goal:** SMS, mobile push, marketing campaigns, or finding
details in an unencrypted email.

### Goal 1.5 — Put cost, rate, and failure controls around GPT-5.6

**Outcome:** A traffic spike, oversized package, retry loop, or abusive customer
cannot create uncontrolled model cost or hide a production incident.

**Scope:**

- Record request ID, account, job, model, reasoning effort, latency, input/output
  tokens, selected visual count, status, and retry count without logging evidence
  contents.
- Enforce server-side package, image, page, and monthly review limits.
- Set per-account and global concurrency limits.
- Alert on elevated provider failures, stuck jobs, unusual latency, token
  outliers, and repeated blocked attempts.
- Add an operator view for current jobs, failures, usage, and storage cleanup.
- Document a safe kill switch that stops new model work without replacing it
  with mock output.

**Done when:**

- Limits are enforced before an avoidable OpenAI request is made.
- An operator can connect a customer-visible failure to a private request record
  without seeing appraisal contents by default.
- Alerts and the kill switch are tested in a non-production environment.
- No API key, raw prompt, extracted evidence, or image data appears in routine
  logs.

**Dependencies:** Goal 1.3.

**Not part of this goal:** Public reliability claims based on the current small
sample or a full analytics warehouse.

### Goal 1.6 — Make retention and deletion automatic and verifiable

**Outcome:** CoAppraiser stores sensitive appraisal material only as long as the
customer and documented policy require.

**Scope:**

- Choose and publish default retention periods for customer uploads, generated
  evidence, model records, deleted accounts, anonymous demos, and backups.
- Schedule demo cleanup rather than relying mainly on visits to `/demo/`.
- Add a scheduled customer-data retention job with dry-run and audit output.
- Verify database deletion and private R2 object deletion together.
- Let customers delete a review and close an account through explicit,
  authenticated confirmation.
- Retain only the minimum fraud-prevention record needed to enforce promotional
  usage; do not retain appraisal contents for that purpose.

**Done when:**

- Automated cleanup runs on a schedule and reports successes and failures.
- Tests verify database, R2, demo, account, and partial-failure behavior.
- Terms, FAQ, README, and the application state the same retention behavior.
- A deletion failure is visible to an operator and retried safely.

**Dependencies:** Goal 1.2 for account closure and Goal 1.5 for operations.

**Not part of this goal:** Claims of certification or regulatory compliance that
have not been independently established.

## Priority 2 — expand evidence coverage without weakening trust

### Goal 2.1 — Expand UAD 3.6 normalization in measured batches

**Outcome:** Preflight recognizes more decision-useful fields from real UAD 3.6
XML while every normalized value remains traceable to an exact source path.

**Why this remains:** The current official-sample gate covers a deliberately
small subset: subject identity/address, condition, quality, and above-grade GLA.
That is a sound foundation, not complete UAD coverage.

**Scope:**

- Build a field coverage matrix from all 12 Appendix D-1 scenarios.
- Select one batch of five to ten high-value fields only after verifying their
  exact XML paths and rendered-report representations.
- Add aliases only when the official samples or documented vendor exports prove
  they are needed.
- Preserve value, source file, exact XML path, parser version, and any
  normalization transform.
- Add clean, missing, alternate-representation, and direct-conflict tests for
  each field.

**Done when:**

- The batch has an explicit coverage table and no guessed field mappings.
- All 12 official scenarios still pass the strict corpus gate.
- Every new cross-source rule has at least one positive and one clean case.
- Unsupported fields remain visibly unsupported rather than being inferred.
- README, `EVAL.md`, and public copy describe the expanded scope precisely.

**Dependencies:** The local Appendix D-1 import described in `EVAL.md`.

**Not part of this goal:** Complete UAD implementation, an official validator,
or copying the publisher's archive into Git.

### Goal 2.2 — Turn Appendix D-1 into a repeatable coverage protocol

**Outcome:** A developer can reproduce the official-sample evaluation from a
fresh clone and understand exactly what passed, what was skipped, and why.

**Scope:**

- Keep the official archive local and verify its publisher URL and hash.
- Parse the scenario matrix into a local, machine-readable manifest where the
  license permits; otherwise document the manual mapping.
- Report paired PDF/XML availability, scenario type, normalized-field coverage,
  skipped material, parser warnings, and source hashes.
- Document how to refresh the corpus when Fannie Mae publishes a new revision.
- Fail clearly when the source archive, expected hash, pairing, or scenario count
  changes.

**Done when:**

- A fresh local run follows one documented import command and one evaluation
  command.
- The report identifies the source revision and all 12 expected scenarios.
- No official source file, private package, or generated corpus is committed.
- A source revision cannot silently replace the evaluated baseline.

**Not part of this goal:** Republishing Fannie Mae or Freddie Mac documents.

### Goal 2.3 — Grow the visual and narrative eval set one labeled case at a time

**Outcome:** Visual and narrative review quality improves from reviewed evidence,
not from a larger unverified prompt.

**Scope:**

- Add one human-reviewed scenario per change, including the expected finding,
  exact visual/report sources, acceptable wording range, and prohibited claims.
- Add a matching clean or ambiguous case to measure false positives.
- Cover poor lighting, duplicate photos, irrelevant images, incomplete photo
  coverage, and a clear photo-to-report conflict over time.
- Score detection, citation, confidence, unrelated findings, professional
  boundaries, latency, and token use separately.
- Use the authorized home photos only in sanitized local eval packages unless the
  owner explicitly approves repository publication.

**Done when:**

- Every accepted visual behavior has a positive and clean case.
- A finding without the correct file or page citation fails the case.
- Low-confidence or diagnostic condition claims are rejected.
- Three repeated paid runs pass before a case becomes a locked release gate.

**Dependencies:** Goals 1.5 and 2.2.

**Not part of this goal:** Inspecting every photo, diagnosing building defects,
  identifying occupants, or treating images as a substitute for inspection.

### Goal 2.4 — Test provider, storage, and load failures deliberately

**Outcome:** Known failure modes have tested recovery behavior before customers
find them.

**Scope:**

- Add an automated OpenAI timeout and rate-limit recovery test.
- Test malformed structured output after the allowed retry.
- Test R2 upload, read, and delete failures.
- Test maximum supported package size and unsupported/protected files.
- Test simultaneous reviews at the configured concurrency limit.
- Test worker termination during each durable processing stage.

**Done when:**

- Each case has a documented expected user state, operator state, retry policy,
  entitlement result, and data-retention result.
- No failure silently falls back to mock AI.
- No retry duplicates findings, notifications, usage charges, or workfile
  versions.
- The full no-cost suite and the bounded paid GPT suite pass after the changes.

**Dependencies:** Goals 1.1, 1.3, and 1.5.

### Goal 2.5 — Grow deterministic checks from evidence, not intuition

**Outcome:** Repeatable checks catch high-confidence package problems cheaply and
leave interpretation to GPT-5.6 and the appraiser.

**Scope:**

- Add a rule only when an official sample, sanitized revision pattern, or labeled
  eval case demonstrates it.
- Version rule behavior and preserve the evidence used by each finding.
- Maintain separate positive, clean, missing-data, and alternate-format cases.
- Measure false positives independently from GPT results.
- Suppress duplicate GPT findings when a deterministic rule already covers the
  same issue.

**Done when:**

- Every rule has a code, version, purpose, evidence contract, positive test,
  clean test, and user-facing action.
- Rule wording does not declare compliance or direct an appraisal conclusion.
- A rule change reruns all affected corpus and regression cases.

**Dependencies:** Goals 2.1 through 2.3.

### Goal 2.6 — Make revised-package comparison decision-useful

**Outcome:** After an appraiser uploads a revised package, the workspace clearly
shows what was fixed, what remains, and what is new, with evidence lineage.

**Scope:**

- Compare findings by stable rule/topic and source evidence rather than title
  text alone.
- Show fixed, still present, new, and materially changed findings.
- Preserve decisions and notes against the version where they were made.
- Distinguish a resolved finding from a finding that merely disappeared because
  evidence was removed.
- Include the comparison in the workfile record.

**Done when:**

- Controlled revised-package fixtures produce exact expected comparisons.
- Source changes are visible and traceable across versions.
- The UI does not claim an issue was fixed when it can only show that the prior
  finding is no longer present.

**Not part of this goal:** Editing the appraisal report inside CoAppraiser.

## Priority 3 — professional operations and polish

### Goal 3.1 — Produce a human-readable workfile review record

**Outcome:** An appraiser can retain a concise professional record without
interpreting raw JSON.

**Scope:**

- Keep JSON as the machine-readable source.
- Add a printable HTML or PDF record containing package/version hashes, source
  manifest, checks, GPT model metadata, findings, appraiser decisions, notes,
  timestamps, and limitations.
- Clearly label the record as a CoAppraiser review record, not the official
  appraisal workfile or a compliance certificate.

**Done when:**

- The human-readable and JSON exports contain the same substantive facts.
- Exports are generated only for the authenticated owner.
- Long filenames, evidence, and notes render correctly on normal paper sizes.
- Export generation has content and visual regression tests.

**Dependencies:** Goal 2.6.

### Goal 3.2 — Add a privacy-respecting operator console

**Outcome:** Support can recover a failed review and answer a customer without
opening appraisal evidence by default.

**Scope:**

- Search by opaque review ID, user email, job state, and provider request ID.
- Show entitlement, subscription, processing milestones, storage state, model
  metadata, notification state, and sanitized errors.
- Allow authorized staff to retry a safe stage, restore an entitlement with a
  reason, and start verified cleanup.
- Audit every staff action and require elevated permission for viewing source
  material.

**Done when:**

- Routine support can diagnose state without seeing report text or photos.
- All mutations are permission-checked, confirmed, and audited.
- Support actions are idempotent and tested.

**Dependencies:** Goals 1.1, 1.3, 1.5, and 1.6.

### Goal 3.3 — Establish a production smoke-test and release routine

**Outcome:** Every deployment is checked the same way before customers depend on
it.

**Scope:**

- Automate Django checks, migration checks, tests, static collection, secret
  scanning, dependency review, and link checks in CI.
- Keep GitHub Pages disabled or remove any unused Pages workflow that generates
  failure emails.
- Add a post-deploy health check for signup/login, private file access, a
  no-cost deterministic package, billing configuration, and job readiness.
- Run periodic desktop and mobile smoke tests for the core Preflight path.
- Document rollback and provider-incident procedures.

**Done when:**

- A broken check blocks deployment or produces an actionable alert.
- Production mock AI, local media storage, unsafe debug mode, and missing required
  secrets fail readiness checks.
- The routine can be followed by someone other than the original developer.

**Dependencies:** Priority 1 production goals.

### Goal 3.4 — Close accessibility and browser-quality gaps

**Outcome:** The public site and authenticated workflow are usable on current
desktop and mobile browsers without layout or keyboard barriers.

**Scope:**

- Test keyboard navigation, focus, form errors, status announcements, contrast,
  reduced motion, zoom, and screen-reader labels.
- Verify current Chrome, Safari, Firefox, Edge, iPhone, and Android layouts.
- Fix overflow, dense evidence cards, long filenames, long decision notes, and
  progress-state announcements.

**Done when:**

- The upload, progress, findings, decision, revision, and workfile paths work by
  keyboard.
- Status changes are announced without forcing visual monitoring.
- Automated accessibility checks and a short manual checklist pass.

**Dependencies:** Goal 1.3 so the final progress interaction is tested.

### Goal 3.5 — Add a measured customer-feedback loop

**Outcome:** The next rule and workflow improvements come from observed customer
friction while appraisal contents remain private.

**Scope:**

- Measure privacy-safe events such as signup, verified account, upload accepted,
  review completed, review failed, finding decision, revised package, workfile
  download, subscription start, and deletion.
- Add an optional per-review usefulness prompt and a way to report an incorrect
  finding without automatically sharing the package.
- Define a consent-based path for a customer to share selected evidence with
  support for debugging.

**Done when:**

- Analytics contain identifiers and state transitions, not appraisal evidence,
  addresses, borrower data, prompts, or photos.
- Consent is explicit before any evidence is shared.
- Product decisions can be tied to measured friction or labeled feedback.

**Dependencies:** Goals 1.2, 1.5, and 1.6.

## Explicitly deferred

These items should not enter the active queue unless the current Preflight
workflow requires them or the product strategy changes:

- official UAD, GSE, lender, AMC, or USPAP validation;
- automated value opinions, comparable selection, or final adjustment advice;
- broad OCR for image-only documents;
- exhaustive inspection of every report page or photograph;
- teams, firm administration, shared assignments, or enterprise SSO;
- native mobile applications;
- direct TOTAL, ACI, ClickFORMS, AMC, or lender integrations;
- additional pricing tiers or unrelated Stripe work;
- autonomous agents that change appraisal data or make professional decisions;
- legacy Revision Response, Market Evidence, or unrelated product modules.

## Recommended execution order

1. Finish the Build Week submission and truthful public copy.
2. Build the durable promotional entitlement and verified account lifecycle.
3. Move processing to a durable worker, then add notifications and usage controls.
4. Lock retention, deletion, and operator recovery.
5. Expand Appendix D-1 normalization and eval coverage in small measured batches.
6. Improve revised-package comparison and the human-readable workfile record.
7. Formalize release, accessibility, and feedback operations.

The product should remain a focused Preflight system throughout this work. More
coverage is useful only when it increases traceable, repeatable confidence without
making the product sound more certain than its evidence.
