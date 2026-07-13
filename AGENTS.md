# AGENTS.md

# CoAppraiser Project Guide for AI Coding Agents

## Project Name

CoAppraiser

## Project Summary

CoAppraiser is a compliance-first AI copilot for residential real estate appraisers.

The product helps appraisers:

- catch likely report issues before delivery
- respond to lender, reviewer, AMC, or client revision requests
- organize support for market conditions and time adjustments
- keep a cleaner AI-assisted workfile
- use AI safely without replacing professional judgment

CoAppraiser is not a full appraisal form-filling platform. It does not replace TOTAL, Appraise-It Pro, ClickFORMS, ACI, DataMaster, Spark, Aivre, MLS systems, or any official GSE compliance API.

The product should work alongside the tools appraisers already use.

The near-term product focus is:

1. Revision Response Agent
2. Workfile Guardian
3. Market Evidence Pack
4. UAD 3.6 Readiness / Issue Explainer
5. AI Skill Library as a secondary feature

The MVP should start simple and useful. Do not overbuild.

---

# Critical Product Positioning

## What CoAppraiser Is

CoAppraiser is a web app that helps appraisers turn messy assignment material into reviewable, defensible workfile artifacts.

Examples:

- A reviewer asks for more support for a GLA adjustment.
- The appraiser pastes the revision request into CoAppraiser.
- CoAppraiser explains what the request is really asking for.
- CoAppraiser drafts a professional response.
- CoAppraiser suggests what evidence the appraiser should verify.
- CoAppraiser creates a workfile note showing what was generated and what still needs appraiser review.

The key product concept is:

> Every AI output should become a workfile artifact, not just a chat response.

## What CoAppraiser Is Not

CoAppraiser is not:

- an automated valuation model
- a value conclusion engine
- a comp selector that replaces the appraiser
- a report signer
- a full desktop appraisal form system
- official UAD validation software
- legal, compliance, or USPAP advice
- a tool that guarantees lender, AMC, GSE, or USPAP compliance

Never write copy or features that imply CoAppraiser determines value, completes an appraisal, guarantees compliance, or replaces appraiser judgment.

---

# Primary Target User

The primary user is a residential real estate appraiser.

They may be:

- a solo fee appraiser
- a lender-panel residential appraiser
- a small appraisal office owner
- a review appraiser
- a trainee appraiser
- a private assignment appraiser handling divorce, estate, tax appeal, or pre-listing work

The user is usually busy, skeptical of hype, and already uses appraisal software.

They do not want another complicated system.

They want fewer revisions, cleaner support, faster report writing, and safer AI use.

---

# Founder Context

The founder is a residential appraiser working in a county assessor environment, not a traditional fee appraiser.

Do not assume the founder already knows every fee-appraiser workflow term.

When adding domain-specific features, use plain labels and explanatory helper text.

Good UI wording:

- "Reviewer comment"
- "Revision request"
- "What the appraiser should verify"
- "Suggested response draft"
- "Workfile note"
- "Support checklist"

Avoid vague labels:

- "AI magic"
- "valuation assistant"
- "automated appraisal"
- "compliance guaranteed"
- "one-click appraisal"

---

# Business Direction

The research-backed business direction is:

CoAppraiser should sell into urgent appraisal pain around:

- UAD 3.6 readiness
- revision response
- report QA
- market evidence and time adjustment support
- workfile documentation
- safe AI use

The site and app should not lead with a generic "AI skill store" message.

The skill store exists, but it is secondary.

The flagship product is:

> CoAppraiser Compliance & Workfile Copilot

Suggested public positioning:

> UAD 3.6 Compliance & Workfile Copilot for Residential Appraisers

Supporting message:

> Catch report issues, prepare defensible support, respond to revisions, and keep a cleaner workfile without replacing your existing appraisal software.

---

# MVP Strategy

Build the app in this order:

## Phase 1: Revision Response Agent

This is the first real MVP.

Why first:

- fastest to build
- easiest for users to understand
- does not require MLS integrations
- does not require official UAD API access
- solves a recurring emotional pain
- works with pasted text

Basic user flow:

1. User creates an Assignment.
2. User opens "Revision Response Agent."
3. User pastes a revision request.
4. User optionally pastes relevant report text or rough notes.
5. User clicks "Generate Response."
6. App returns:
   - issue summary
   - what the reviewer/client is asking for
   - suggested professional response
   - optional report/addendum language
   - support checklist
   - workfile note
   - verification warnings
7. User can save the output as an artifact.
8. AI action is logged in the assignment workfile.

This is the first product to build.

## Phase 2: Workfile Guardian

Workfile Guardian is the shared backbone.

It logs:

- uploaded documents
- pasted source text
- AI prompts
- generated outputs
- user-approved outputs
- verification checklists
- source notes
- workfile artifacts

Every workflow should write to the workfile log.

The Workfile Guardian page should show:

- assignment summary
- documents
- AI action history
- saved artifacts
- verification checklist
- export options

## Phase 3: Market Evidence Pack

Market Evidence Pack uses appraiser-provided MLS CSV or sales data.

It helps organize:

- sale date trends
- sale price trends
- days-on-market trends
- list-to-sale ratio trends
- market condition support
- time adjustment support
- caution flags
- report-ready market language

Important boundary:

CoAppraiser may summarize evidence and suggest support language.

CoAppraiser must not tell the appraiser what final adjustment to use.

Good wording:

> The data may support further review for a possible market conditions adjustment. The appraiser should verify applicability to the subject's market segment and selected comparable sales.

Bad wording:

> Use a 1.2% monthly adjustment.

## Phase 4: UAD 3.6 Readiness / Issue Explainer

Start with readiness and issue explanation.

Do not claim official UAD validation.

Level 1:

- UAD 3.6 readiness checklist
- report text review
- issue explanation

Level 2:

- user pastes UAD issue text
- CoAppraiser explains the likely meaning
- CoAppraiser suggests what to verify

Level 3 later:

- XML-aware review if users can upload/export UAD XML
- still unofficial unless integrated with official compliance APIs

## Phase 5: AI Skill Library

Skill Library is secondary.

It can include lightweight downloadable or in-app workflows:

- Revision Response Skill
- Report QA Skill
- Messy Notes to Report Language
- Comp Selection Defense Skill
- MLS Remarks Extractor Skill
- Market Conditions Paragraph Builder
- Workfile Documentation Skill
- Appraiser AI Policy Builder

Do not let the skill library distract from the main copilot product.

---

# Core Domain Glossary

Use this glossary to understand the appraisal workflow.

## Appraiser

A professional who develops an opinion of value for real property. In this product, we are focused on residential real estate appraisers.

## Subject Property

The property being appraised.

## Comparable Sale / Comp

A sold property used to help analyze the subject property's market value.

CoAppraiser may help organize comp discussion, but the appraiser must decide which comps are appropriate.

## Sales Comparison Approach

A common appraisal method where the appraiser compares the subject property to similar recently sold properties and adjusts for differences.

## Adjustment

A dollar or percentage change applied to a comparable sale to account for differences from the subject property.

Examples:

- gross living area
- condition
- quality
- site size
- view
- garage
- outbuilding
- basement finish
- location
- market conditions / time

CoAppraiser can help explain or support adjustments, but must not make final adjustment decisions.

## GLA

Gross Living Area.

This usually means finished above-grade residential living area. Appraisers often get revision requests asking them to support GLA adjustments.

## UAD

Uniform Appraisal Dataset.

A structured data standard used in mortgage appraisal reporting.

## UAD 3.6

The newer UAD reporting structure and data standard. It is a major market forcing function for residential appraisers.

CoAppraiser should focus on UAD 3.6 readiness and issue explanation, not official validation unless a proper official integration exists.

## USPAP

Uniform Standards of Professional Appraisal Practice.

Appraisers are responsible for complying with USPAP. CoAppraiser does not guarantee USPAP compliance.

## Workfile

The appraiser's retained file of data, notes, analysis, sources, and support used in the appraisal assignment.

CoAppraiser should help create and organize workfile artifacts.

## Revision Request

A request from a lender, AMC, reviewer, or client asking the appraiser to clarify, correct, expand, or support something in the appraisal report.

Revision Response Agent is the first MVP product.

## ROV

Reconsideration of Value.

A process where a party asks for reconsideration based on additional information or alleged issues.

CoAppraiser may help organize responses, but must not act as an advocate or guarantee outcome.

## AMC

Appraisal Management Company.

A company that manages appraisal orders between lenders and appraisers.

## Market Conditions

The state of the market as of the effective date.

May include:

- increasing prices
- declining prices
- stable prices
- supply/demand
- inventory
- days on market
- list-to-sale ratio
- buyer/seller conditions

## Time Adjustment

An adjustment to comparable sales to account for market movement between the comparable sale date and the effective date of the appraisal.

This is a high-risk, revision-prone area.

## Effective Date

The date as of which the opinion of value applies.

Market evidence and comparable sales should be analyzed in relation to this date.

## Engagement Letter / Order

The assignment order or instructions from the client.

May contain:

- assignment type
- client requirements
- due date
- property address
- special conditions
- report type
- intended use
- intended user

---

# Core Product Modules

## 1. Revision Response Agent

Purpose:

Help appraisers respond to revision requests faster and more professionally.

Inputs:

- reviewer comment
- lender revision request
- AMC condition
- rough appraiser notes
- relevant report excerpt
- comp data
- adjustment explanation
- market condition notes

Outputs:

- plain-English issue summary
- what the request is really asking for
- professional portal response
- optional report/addendum language
- support checklist
- workfile note
- risk flags
- verification checklist

Important behavior:

The app should ask for missing context only when necessary.

If enough information exists, generate a useful draft and mark what needs verification.

Do not produce aggressive, defensive, or argumentative responses.

The tone should be professional and neutral.

Good output structure:

1. Issue Summary
2. Recommended Action
3. Draft Response
4. Optional Report Language
5. Workfile Note
6. What to Verify
7. Risk Flags

Example revision request:

> Please provide additional support for the GLA adjustment.

Good CoAppraiser response:

- Explain that the reviewer is asking for support, not just a restatement.
- Suggest reviewing paired sales, market extraction, prior support, or comp grid consistency.
- Draft a concise response.
- Create a workfile note.
- Warn the appraiser not to imply unsupported precision.

---

## 2. Workfile Guardian

Purpose:

Create a defensible record of AI-assisted appraisal work.

Inputs:

- uploaded files
- pasted text
- generated outputs
- user edits
- selected final artifacts
- source references
- verification notes

Outputs:

- AI action log
- source log
- artifact list
- verification checklist
- exportable workfile packet
- assignment history

Critical concept:

Every AI workflow must write to the Workfile Guardian.

The workfile should separate:

- source input
- AI draft
- appraiser-approved output
- appraiser verification notes

Never overwrite original AI output silently.

If the user edits or approves output, keep the earlier version in the log.

---

## 3. Market Evidence Pack

Purpose:

Help appraisers organize support for market conditions and time adjustments from appraiser-provided data.

Inputs:

- MLS CSV export
- sale date
- sale price
- list price
- close date
- days on market
- property type
- location / neighborhood / market area
- GLA
- lot size
- selected comp list
- effective date
- appraiser notes

Outputs:

- market trend summary
- basic charts or tables
- sale date distribution
- price trend observations
- DOM trend observations
- list-to-sale ratio observations
- possible outlier flags
- caution flags
- market condition paragraph draft
- workfile evidence memo

Important behavior:

Use careful language.

CoAppraiser should not determine the final adjustment.

CoAppraiser should say what the data appears to show and what the appraiser should verify.

Good language:

> The provided sales data appears to show upward price pressure during the analyzed period. The appraiser should verify whether this trend is applicable to the subject's market segment, property type, and selected comparable sales.

Bad language:

> Apply a 1.5% monthly market adjustment.

---

## 4. UAD 3.6 Compliance Copilot

Purpose:

Help appraisers prepare for UAD 3.6 and understand likely issue areas.

Inputs:

- draft report text
- UAD error or issue text
- engagement letter
- assignment notes
- comp notes
- report sections
- revision request related to UAD fields

Outputs:

- issue explanation
- severity estimate
- suggested review steps
- likely report section to inspect
- support checklist
- workfile note

Important boundary:

Unless official API integration exists, this is not official UAD validation.

Use labels like:

- "UAD 3.6 Readiness Review"
- "Issue Explainer"
- "Pre-Delivery Review"
- "Potential Issue"

Avoid labels like:

- "Certified UAD Validator"
- "GSE compliance approved"
- "Guaranteed compliant"

---

## 5. AI Skill Library

Purpose:

Provide smaller AI workflows as supporting tools.

Potential skills:

- Revision Response Skill
- Report QA Skill
- Messy Notes to Report Language
- Comp Selection Defense Skill
- MLS Remarks Extractor Skill
- Market Conditions Paragraph Builder
- Public Record / MLS Conflict Checker
- Workfile Documentation Skill
- Appraiser AI Policy Builder

The skill library should be organized but not treated as the main app.

---

# Recommended Tech Stack

The founder prefers:

- Python
- Django
- HTMX
- HTML
- Tailwind CSS
- simple readable code

Use this stack unless explicitly told otherwise.

## Preferred Architecture

Django app with server-rendered templates.

Use HTMX for lightweight interactivity.

Use Tailwind for styling.

Avoid heavy frontend frameworks.

Do not introduce React unless explicitly requested.

## Suggested Django Apps

Possible app structure:

- accounts
- assignments
- documents
- ai_actions
- artifacts
- revision_agent
- market_evidence
- uad_readiness
- workfile
- marketing

Keep it simple.

Do not split into too many apps too early.

A practical initial structure:

- `core`
- `assignments`
- `ai_tools`
- `marketing`

That may be enough for MVP.

---

# Suggested Data Model

Start simple.

## Assignment

Represents one appraisal assignment or project.

Fields:

- user
- title
- property_address
- assignment_type
- client_name optional
- effective_date optional
- status
- created_at
- updated_at

## Document

Represents uploaded or pasted source material.

Fields:

- assignment
- document_type
- title
- file
- original_filename
- extracted_text
- pasted_text
- created_at

Document types:

- report_pdf
- revision_request
- engagement_letter
- mls_csv
- public_record
- comp_notes
- market_notes
- uad_issue
- other

## AIActionLog

Represents every AI request and response.

Fields:

- assignment
- action_type
- input_text
- input_documents
- system_instruction_snapshot
- model_name
- output_json
- output_text
- created_at
- created_by

Action types:

- revision_response
- workfile_note
- market_evidence_pack
- uad_issue_explainer
- report_qa
- notes_to_language
- other

## OutputArtifact

Represents a saved deliverable.

Fields:

- assignment
- title
- artifact_type
- content
- source_action
- approved_by_user
- user_edited_content
- created_at
- updated_at

Artifact types:

- revision_response
- report_language
- workfile_note
- support_checklist
- market_evidence_memo
- uad_issue_summary
- qa_punch_list

## VerificationItem

Represents something the appraiser must verify.

Fields:

- assignment
- artifact optional
- description
- status
- created_at
- completed_at

Status:

- open
- verified
- not_applicable
- needs_more_info

---

# UI / UX Requirements

Keep the app simple.

The user should not feel like they are configuring a complicated enterprise system.

## Main Navigation

For logged-in app:

- Dashboard
- Assignments
- Revision Agent
- Market Evidence
- UAD Readiness
- Workfile
- Settings

For public marketing site:

- Solutions
- UAD 3.6 Checklist
- Skill Library
- Pricing
- Early Access

## Dashboard

Show:

- recent assignments
- quick action: New Assignment
- quick action: New Revision Response
- recent AI actions
- open verification items

## Assignment Detail Page

Should show:

- assignment summary
- uploaded documents
- available workflows
- saved artifacts
- verification checklist
- AI action log

## Revision Agent Page

Fields:

- revision request textarea
- relevant report excerpt textarea
- rough appraiser notes textarea
- optional assignment selector
- generate button

Output cards:

- Issue Summary
- Recommended Action
- Draft Response
- Optional Report Language
- Workfile Note
- What to Verify
- Risk Flags

Buttons:

- Save to Workfile
- Copy Response
- Copy Report Language
- Mark as Reviewed
- Export

## Design Style

Use:

- light background
- navy text
- blue/purple accent gradients
- rounded cards
- subtle shadows
- small badges
- app-like panels
- clean spacing
- mobile-first layout

Avoid:

- dark enterprise dashboard look
- cluttered tables everywhere
- fake testimonials
- fake compliance badges
- fake lender logos
- exaggerated AI claims

---

# AI Output Rules

All AI workflows must follow these rules.

## Global AI Guardrails

The AI must not:

- determine value
- select final comps as a replacement for appraiser judgment
- make unsupported adjustment conclusions
- claim compliance
- guarantee UAD, USPAP, lender, AMC, FHA, VA, Fannie Mae, or Freddie Mac acceptance
- encourage discriminatory language
- produce protected-class analysis
- pretend to have verified facts it has not verified
- fabricate sources, data, report sections, or exhibits

The AI must:

- clearly mark drafts as drafts
- explain what the appraiser should verify
- separate source material from generated language
- use cautious, professional appraisal language
- log outputs to the assignment workfile
- create verification items when support is missing

## Preferred Output Format

When calling an LLM, request structured JSON internally.

Then render it in the UI.

Example structure for Revision Response Agent:

```json
{
  "issue_summary": "",
  "request_type": "",
  "recommended_action": "",
  "draft_response": "",
  "optional_report_language": "",
  "workfile_note": "",
  "verification_items": [],
  "risk_flags": [],
  "missing_information": []
}

Add this section to `AGENTS.md` after **Recommended Tech Stack**.

````md
---

# Technical Build Philosophy

This project should be built as a practical Django product, not an over-engineered startup demo.

The founder prefers:

- Django
- Python
- HTMX
- Tailwind CSS
- PostgreSQL
- Railway
- server-rendered pages
- simple readable code
- small focused views
- boring reliable architecture

The technical goal is:

> Build the smallest clean system that can support real appraiser workflows, save AI outputs, preserve workfile history, and deploy easily.

Do not chase clever architecture.

Do not build a generic AI platform.

Do not introduce unnecessary services.

Do not split code into complex layers before the product needs it.

Less code is better when the decision is clear.

---

# Preferred Stack

## Backend

Use Django.

Django should handle:

- routing
- authentication
- models
- forms
- templates
- file uploads
- admin
- permissions
- database access
- server-rendered pages

Use Django’s built-in tools before adding packages.

Good default choices:

- Django auth for users
- Django forms or ModelForms
- Django templates
- Django messages framework
- Django admin
- Django storage abstraction
- Django management commands

Avoid:

- FastAPI for the main app
- Node backend
- unnecessary microservices
- GraphQL
- complex API-first design
- premature service layers

This is a workflow app. Django is enough.

---

# Frontend

Use server-rendered Django templates with HTMX for small interactions.

Use HTMX for:

- submitting forms without full page reloads
- refreshing generated AI output panels
- inline artifact saving
- updating verification item status
- loading assignment panels
- simple modal content if needed

Do not use React, Vue, Svelte, Next.js, or other frontend frameworks unless explicitly requested.

The UI should feel like a clean app, but the code should remain simple.

Preferred frontend pattern:

```html
<form hx-post="{% url 'revision_agent:generate' assignment.id %}"
      hx-target="#revision-output"
      hx-swap="innerHTML">
  ...
</form>

<div id="revision-output">
  {% include "ai_tools/partials/revision_output.html" %}
</div>
````

Use partial templates for HTMX responses.

Good template structure:

```text
templates/
  base.html
  marketing/
  assignments/
  ai_tools/
    revision_agent.html
    market_evidence.html
    uad_readiness.html
    partials/
      revision_output.html
      artifact_card.html
      verification_item.html
```

---

# Styling

Use Tailwind CSS.

Keep the current CoAppraiser visual style:

* light cream or white background
* dark navy text
* blue/purple accents
* rounded cards
* soft shadows
* simple badges
* clean spacing
* mobile-first layout
* app-like panels

Avoid:

* dark enterprise dashboards
* dense admin-table layouts
* giant walls of text
* overly animated UI
* complicated component systems
* custom CSS unless Tailwind becomes awkward

Use consistent reusable layout patterns:

* page container
* card
* badge
* section header
* primary button
* secondary button
* warning box
* output card
* verification checklist item

Do not create ten different card styles.

---

# Database

Use PostgreSQL.

Development may use SQLite only for quick local setup if needed, but the production target is PostgreSQL on Railway.

Core database priorities:

* preserve user input
* preserve AI output
* preserve workfile logs
* preserve original source material
* track user approval/editing
* prevent users from accessing other users’ assignments

Do not optimize too early.

Do not create complex reporting tables until actual usage demands it.

Use normal Django models first.

---

# Hosting

Deploy on Railway.

Railway should run:

* Django web process
* PostgreSQL database
* environment variables
* static file collection
* media/file storage strategy

Use environment variables for secrets.

Required environment variables:

```text
SECRET_KEY
DEBUG
ALLOWED_HOSTS
DATABASE_URL
OPENAI_API_KEY
ANTHROPIC_API_KEY
COAPPRAISER_LLM_PROVIDER
COAPPRAISER_LLM_MODEL
```

Only one LLM provider is needed at first.

If multiple providers are supported, keep the interface simple.

---

# Static and Media Files

Use WhiteNoise for static files unless the project already has another simple working approach.

For uploaded files:

MVP can use local media storage in development.

For production, prefer a Railway-compatible object storage option when file uploads become real.

Do not store confidential appraisal documents in public static directories.

Uploaded files must not be publicly accessible by guessing a URL.

All document access should be permission-checked.

---

# App Structure

Keep the app structure tight.

A good starting structure:

```text
coappraiser/
  config/
    settings.py
    urls.py
    wsgi.py
    asgi.py

  apps/
    accounts/
    assignments/
    ai_tools/
    documents/
    marketing/
    workfile/

  templates/
  static/
  media/
  manage.py
```

If the current repo has a simpler structure, do not rewrite everything just to match this.

Prefer fewer apps early.

Acceptable MVP structure:

```text
apps/
  core/
  assignments/
  ai_tools/
  marketing/
```

Do not create a new Django app for every tiny feature.

Use new apps only when the code has a clear domain boundary.

---

# Coding Style

Write boring, readable Python.

Prefer this:

```python
def assignment_detail(request, pk):
    assignment = get_object_or_404(
        Assignment,
        pk=pk,
        user=request.user,
    )
    return render(request, "assignments/detail.html", {
        "assignment": assignment,
    })
```

Over this:

```python
class EnterpriseAssignmentContextOrchestratorView(...)
```

Use simple functions until class-based views clearly reduce code.

Keep names obvious.

Good names:

* `Assignment`
* `Document`
* `AIActionLog`
* `OutputArtifact`
* `VerificationItem`
* `generate_revision_response`
* `create_workfile_note`
* `parse_market_csv`

Bad names:

* `Processor`
* `Manager`
* `Handler`
* `Orchestrator`
* `Magic`
* `Engine`

Avoid abstract naming unless there are multiple real implementations.

---

# Less Code, Better Decisions

Before adding code, ask:

1. Does this help the appraiser finish a real workflow?
2. Does this preserve the workfile trail?
3. Does this reduce revision risk or support review?
4. Can Django already do this?
5. Can this be one view, one form, and one template?

Prefer:

* one clear model over five clever models
* one readable view over a generic framework
* one template partial over a JavaScript state machine
* one plain service function over a class hierarchy
* one useful workflow over many half-built features

Do not build infrastructure for imaginary scale.

---

# Service Functions

Use service functions for AI workflows and file parsing when it keeps views clean.

Good pattern:

```text
apps/
  ai_tools/
    services/
      revision_response.py
      market_evidence.py
      uad_issue_explainer.py
      llm_client.py
```

A view should handle:

* permissions
* form validation
* calling the service
* saving results
* rendering response

A service should handle:

* prompt construction
* LLM calls
* parsing structured output
* fallback mock output
* business-specific output formatting

Keep services simple.

Do not create a large object-oriented framework.

---

# LLM Integration

Create one small LLM client wrapper.

Suggested file:

```text
apps/ai_tools/services/llm_client.py
```

The LLM wrapper should:

* read provider/model from environment variables
* accept a system prompt
* accept user input
* optionally request JSON output
* return plain Python data
* handle missing API keys with a mock response in development
* not expose API keys
* not print confidential prompts to logs

Example interface:

```python
def run_llm_json(system_prompt: str, user_prompt: str, schema_name: str) -> dict:
    ...
```

Keep the app independent from one provider where practical, but do not overbuild provider abstraction.

Start with one provider.

Add another only when needed.

---

# AI Output Storage

Every AI call must be saved.

Minimum saved fields:

* assignment
* action type
* input text
* system instruction snapshot
* model name
* raw output
* parsed output
* created by
* created at

Never only show an AI response in the browser without saving it.

The product value depends on workfile history.

---

# File Parsing

Start with simple file support.

MVP file types:

* PDF
* TXT
* CSV

Use practical Python packages:

* `pypdf` or `pdfplumber` for PDF text extraction
* `pandas` for CSV analysis
* Python standard library where possible

Do not build OCR in MVP unless explicitly requested.

Do not attempt advanced PDF layout reconstruction early.

For appraisal reports, extracted text does not need to be perfect at first. The user can paste the relevant section manually.

---

# Market Evidence CSV Handling

Use pandas for CSV ingestion.

The first version should:

* accept uploaded CSV
* show detected columns
* let user map key fields if needed
* summarize sale count
* summarize sale date range
* summarize median sale price
* summarize average/median DOM if present
* summarize list-to-sale ratio if list price exists
* flag missing important columns
* generate a simple workfile memo

Do not try to support every MLS export perfectly on day one.

Start with flexible column detection.

Example likely column names:

```text
sale_price, sold_price, close_price, price
sale_date, sold_date, close_date
list_price, original_list_price
dom, days_on_market
gla, living_area, sqft
site_size, lot_size, acres
address, street_address
city
remarks, public_remarks, marketing_remarks
```

If required fields are missing, show a useful message and ask the user to map columns or upload a different file.

---

# Permissions

Security matters because appraisal assignments can contain confidential information.

Every user-owned object must be permission checked.

Always filter by `user=request.user` through the assignment relationship.

Good:

```python
assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
```

Bad:

```python
assignment = Assignment.objects.get(pk=pk)
```

Do not expose uploaded files without checking ownership.

Do not create public share links in MVP.

---

# Forms

Use Django forms or ModelForms.

Keep forms simple.

Recommended forms:

* `AssignmentCreateForm`
* `DocumentUploadForm`
* `RevisionResponseForm`
* `MarketEvidenceUploadForm`
* `UADIssueExplainerForm`
* `VerificationItemForm`

Use clear help text.

Example:

```python
revision_request = forms.CharField(
    widget=forms.Textarea,
    help_text="Paste the reviewer, lender, AMC, or client revision request exactly as received.",
)
```

The founder and users may not know every appraisal software term, so helper text matters.

---

# Templates

Use simple templates and partials.

Recommended pattern:

```text
templates/
  base.html
  components/
    badge.html
    button.html
    card.html
    empty_state.html
    disclaimer.html

  assignments/
    list.html
    detail.html
    form.html

  ai_tools/
    revision_response.html
    uad_issue_explainer.html
    market_evidence.html
    partials/
      revision_response_result.html
      market_summary_result.html
      uad_issue_result.html

  workfile/
    detail.html
    export.html
```

Do not create a complex custom component framework.

A few includes are fine.

---

# Error Handling

Errors should help the user keep moving.

Bad error:

> Failed.

Good error:

> CoAppraiser could not read this PDF. You can paste the relevant report section manually below.

For LLM failures:

> The AI response could not be generated right now. Your input was saved, and you can try again.

For CSV failures:

> CoAppraiser could not identify a sale price column. Please select the correct column or upload a CSV with sale price data.

---

# Development Defaults

During development:

* allow mock LLM responses
* allow local file storage
* allow simple email links
* skip billing
* skip team accounts
* skip official integrations
* skip background queues unless needed

Do not block MVP progress on:

* Stripe
* Celery
* S3
* multi-tenant teams
* official UAD API
* MLS integrations
* PDF-perfect parsing

Those can come later.

---

# When to Add Complexity

Only add Celery/background jobs if:

* file processing is slow
* AI calls timeout
* exports take too long
* users need async status updates

Only add S3/object storage if:

* production file uploads are enabled
* local Railway storage is not sufficient
* user files must persist reliably

Only add Stripe if:

* the core workflow is useful
* early users have tested it
* pricing is ready

Only add teams/organizations if:

* solo workflow works
* multiple real users ask for shared workspaces

Only add official UAD integration if:

* the issue explainer is useful
* users can provide real UAD issue data
* a valid integration path exists

---

# Local Development

Prefer simple setup.

Expected commands should be something like:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

For Tailwind, use the simplest setup already present.

If Tailwind is CDN-based for MVP, that is acceptable.

If using a Tailwind build process, document the exact command.

Do not create a complicated asset pipeline unless needed.

---

# Railway Deployment Notes

The app should be Railway-friendly.

Recommended:

* use `DATABASE_URL`
* use `python manage.py collectstatic --noinput`
* use WhiteNoise for static files
* set `ALLOWED_HOSTS`
* set `CSRF_TRUSTED_ORIGINS`
* use environment variables for secrets
* keep Procfile/start command simple

Example start command:

```bash
gunicorn config.wsgi:application
```

or whatever matches the actual Django project module.

Do not hardcode local paths.

Do not hardcode secrets.

---

# Testing Philosophy

Add basic tests around core workflow.

Minimum useful tests:

* user can create assignment
* user cannot view another user's assignment
* revision response form creates AIActionLog
* revision response form creates OutputArtifact
* revision response form creates VerificationItems
* workfile page lists saved artifacts
* document upload belongs to assignment
* missing LLM API key returns mock output in debug mode

Do not write fragile tests for exact AI wording.

Test structure and persistence, not prose.

---

# Admin

Use Django admin to inspect early data.

Register:

* Assignment
* Document
* AIActionLog
* OutputArtifact
* VerificationItem

Admin is useful for debugging and early customer support.

Do not build a custom admin dashboard before the basic app works.

---

# What Good Code Looks Like Here

Good CoAppraiser code is:

* easy to read
* easy to delete
* easy to deploy
* explicit about permissions
* explicit about AI guardrails
* careful with user data
* organized by workflow
* not abstract before necessary

The best code for this project helps an appraiser complete one workflow with confidence.

If code does not support revision response, workfile logging, market evidence, UAD readiness, or saved artifacts, question whether it belongs in the MVP.

## Local Preview

From this folder:

```powershell
python -m http.server 8006 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8006
```

Factory Console also knows this command and can start the local static server.

## Editing Guidelines

- Keep links root-relative so folder pages work under the local static server and production domain.
- Preserve the static-site structure unless the user asks for a framework or build system.
- Update `sitemap.xml` when adding or removing public pages.
- Keep appraisal and compliance language careful, defensible, and non-overpromising.
- Avoid presenting AI output as a substitute for appraiser judgment, USPAP compliance, or lender-specific requirements.
- Reuse existing CSS classes and layout patterns before adding new ones.
- Check mobile layout when changing navigation, hero sections, cards, or grids.

## Verification

For content-only edits, inspect the changed pages in a browser.

For local serving, run:

```powershell
python -m http.server 8006 --bind 127.0.0.1
```

Then confirm that the home page and any edited folder pages load without broken links or missing styles.
