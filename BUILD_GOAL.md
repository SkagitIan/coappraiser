I would give Codex one top-level outcome, then force it to work in phases without drifting. Save this as `BUILD_GOAL.md` at the repo root or paste it directly into Codex.

````md
# CoAppraiser End-to-End Build Goal

## Primary Goal

Build CoAppraiser from the existing static frontend into a complete, deployable Django application.

CoAppraiser is a compliance-first AI copilot for residential real estate appraisers. It works alongside existing appraisal software and helps users:

- respond to revision requests
- review possible UAD 3.6 issues
- organize market-condition evidence
- create traceable workfile artifacts
- use reusable appraisal-specific AI skills

The finished project must work end to end:

1. A visitor can view the existing marketing site.
2. A user can create an account and sign in.
3. A user can create an appraisal assignment.
4. A user can upload or paste assignment material.
5. A user can run an AI skill.
6. The generated output is displayed in a useful structured interface.
7. Inputs, outputs, sources, and verification items are saved.
8. The user can edit and approve an output.
9. The approved result becomes a workfile artifact.
10. The user can view and export the assignment workfile.
11. The application can be deployed to Railway with PostgreSQL.

Do not stop after creating scaffolding. Complete the first production-shaped workflow from the public homepage through saved AI output.

---

# Product Boundaries

CoAppraiser is not:

- an automated valuation model
- a final opinion-of-value generator
- a replacement for the appraiser
- official UAD validation software
- a replacement for TOTAL, ClickFORMS, ACI, Appraise-It Pro, DataMaster, Spark, or MLS software
- a system that guarantees USPAP, GSE, lender, AMC, FHA, or VA compliance

CoAppraiser supports professional work. The appraiser remains responsible for verification, analysis, compliance, and final conclusions.

Every generated output must be clearly marked:

> Draft language. Review and verify before use.

UAD-related output must also state:

> UAD readiness support only. Not official GSE validation.

---

# Existing Frontend

The repo already contains a static HTML, JavaScript, and Tailwind marketing site.

Before changing anything:

1. Inspect the entire repo.
2. Identify the current homepage, shared styles, scripts, images, navigation, and page structure.
3. Preserve the current visual identity.
4. Reuse the existing frontend instead of replacing it with a generic Django theme.
5. Move existing static pages into Django templates where appropriate.
6. Keep working public URLs stable when practical.

Current design direction:

- light white or cream background
- dark navy text
- blue and purple accents
- soft gradients
- rounded cards
- subtle shadows
- clean SaaS layout
- mobile-first responsive design
- app-like interface panels

Do not introduce React, Vue, Next.js, or another frontend framework.

Use:

- Django templates
- HTMX
- Tailwind CSS
- minimal vanilla JavaScript

---

# Required Technology

## Backend

- Python
- Django
- PostgreSQL
- Django authentication
- Django forms
- Django templates
- Django admin

## Frontend

- HTMX
- Tailwind CSS
- minimal vanilla JavaScript

## Data and file processing

- pandas for CSV processing
- pypdf or pdfplumber for basic PDF text extraction
- Python standard library where practical

## Deployment

- Railway
- PostgreSQL on Railway
- Gunicorn
- WhiteNoise for static files
- environment variables for secrets

Do not introduce microservices, GraphQL, an API-first architecture, Celery, Redis, or object storage during the first build unless a real blocking requirement appears.

---

# Architecture Principle

Build the smallest coherent system that supports real workflows.

Prefer:

- one clear view over a framework
- one service function over a class hierarchy
- one useful model over several abstract models
- server-rendered HTML over frontend state management
- explicit code over generic engines
- fewer files with clear ownership
- normal Django patterns

Do not build infrastructure for hypothetical scale.

---

# Recommended Project Structure

Use the existing structure when sensible. A reasonable target is:

```text
coappraiser/
├── manage.py
├── AGENTS.md
├── BUILD_GOAL.md
├── README.md
├── requirements.txt
├── Procfile
├── .env.example
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/
│   ├── assignments/
│   ├── ai_tools/
│   ├── workfile/
│   └── marketing/
├── skills/
│   ├── README.md
│   ├── revision-response/
│   │   └── SKILL.md
│   ├── workfile-note/
│   │   └── SKILL.md
│   ├── uad-issue-explainer/
│   │   └── SKILL.md
│   ├── market-evidence/
│   │   └── SKILL.md
│   └── report-qa/
│       └── SKILL.md
├── tools/
│   ├── README.md
│   ├── pdf-text-extractor.md
│   ├── csv-market-analyzer.md
│   ├── artifact-writer.md
│   └── workfile-logger.md
├── templates/
├── static/
└── tests/
````

Do not reorganize working code solely to match this example.

---

# Core Domain Model

## Assignment

Represents one appraisal assignment.

Fields should include:

* user
* title
* property address
* assignment type
* client name, optional
* effective date, optional
* status
* created date
* updated date

## Document

Represents uploaded or pasted source material.

Fields:

* assignment
* title
* document type
* uploaded file, optional
* pasted text, optional
* extracted text
* original filename
* created date

Supported MVP types:

* revision request
* report PDF
* report excerpt
* engagement letter
* MLS CSV
* appraiser notes
* UAD issue
* public record
* other

## AIActionLog

Represents one AI-assisted action.

Fields:

* assignment
* skill slug
* action type
* input snapshot
* selected document references
* system prompt snapshot
* model provider
* model name
* raw response
* parsed response
* status
* created by
* created date

Never discard the original input or raw generated response.

## OutputArtifact

Represents a useful saved deliverable.

Fields:

* assignment
* title
* artifact type
* source AI action
* original generated content
* user-edited content
* approval status
* approved date
* created date
* updated date

Artifact types may include:

* revision response
* report addendum language
* workfile note
* support checklist
* UAD issue summary
* market evidence memo
* QA punch list

## VerificationItem

Represents something the appraiser must confirm.

Fields:

* assignment
* related artifact, optional
* description
* status
* user note
* created date
* completed date

Statuses:

* open
* verified
* needs more information
* not applicable

---

# Skill System

Skills must be stored as version-controlled Markdown files under `/skills`.

Each skill must have a `SKILL.md` file with YAML front matter and detailed instructions.

Example structure:

```md
---
name: Revision Response
slug: revision-response
category: revisions
version: 1.0.0
status: active
description: Turn a reviewer or lender revision request into a structured response package.
input_types:
  - revision_request
  - report_excerpt
  - appraiser_notes
output_types:
  - issue_summary
  - recommended_action
  - draft_response
  - report_language
  - workfile_note
  - verification_items
---

# Purpose

Explain the workflow purpose.

# Required Inputs

Explain required and optional inputs.

# Guardrails

List what the model must not do.

# Procedure

Define the exact analysis steps.

# Output Schema

Define the required JSON structure.

# Appraiser Verification

Define what must be manually reviewed.

# Example Input

Provide a realistic example.

# Example Output

Provide a realistic structured example.
```

Markdown files are the source of truth for skill instructions.

Build a small skill loader that:

1. scans `/skills/*/SKILL.md`
2. reads YAML metadata
3. loads the Markdown body
4. validates required metadata
5. makes active skills available in the application
6. exposes the skill name, description, inputs, and outputs to templates
7. passes the detailed skill instructions to the LLM service

Do not put all skill prompts directly inside Django views.

Do not build a complex marketplace or plugin architecture yet.

---

# Tool Documentation

Create Markdown documentation under `/tools` for deterministic application capabilities.

Initial tools:

## PDF Text Extractor

Purpose:

* extract basic text from uploaded PDFs
* return a useful error when extraction fails
* allow users to paste text manually as fallback

## CSV Market Analyzer

Purpose:

* read uploaded MLS CSV files
* detect likely columns
* calculate basic descriptive statistics
* return structured data for the Market Evidence skill

## Artifact Writer

Purpose:

* turn structured AI output into saved artifacts
* preserve original and edited versions
* create verification items

## Workfile Logger

Purpose:

* create traceable records of sources, AI actions, outputs, approvals, and verification

These files document what the tools do, their inputs, outputs, limitations, and expected error behavior.

The initial tools are internal Python services, not MCP tools.

---

# LLM Integration

Create one small provider wrapper.

Suggested location:

```text
apps/ai_tools/services/llm_client.py
```

Required interface:

```python
def run_skill(
    *,
    system_prompt: str,
    user_prompt: str,
    output_schema: dict,
) -> dict:
    ...
```

Requirements:

* provider and model come from environment variables
* initially support one real provider
* keep the code simple enough to add another later
* request structured JSON output
* validate the response
* store raw and parsed responses
* do not log confidential prompt content to the console
* return understandable errors
* provide mock output when no API key exists and `DEBUG=True`

Environment variables:

```text
SECRET_KEY
DEBUG
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
DATABASE_URL
OPENAI_API_KEY
ANTHROPIC_API_KEY
COAPPRAISER_LLM_PROVIDER
COAPPRAISER_LLM_MODEL
```

Only one provider must work in the MVP.

---

# First Complete Workflow

The first end-to-end workflow is the Revision Response Agent.

Do not move to advanced workflows until this works completely.

## User Flow

1. User signs in.
2. User creates an assignment.
3. User opens the assignment.
4. User selects Revision Response Agent.
5. User enters:

   * revision request
   * relevant report excerpt, optional
   * appraiser notes, optional
6. User submits the form with HTMX.
7. The server loads `skills/revision-response/SKILL.md`.
8. The server builds the structured prompt.
9. The LLM returns structured JSON.
10. An AIActionLog is saved.
11. OutputArtifact records are created.
12. VerificationItem records are created.
13. Results appear without a full page reload.
14. User can:

* copy the draft response
* edit the response
* approve the response
* save it to the workfile
* mark verification items complete

15. The assignment workfile shows the complete history.

## Required Output Sections

* Issue Summary
* What the Request Is Asking For
* Recommended Action
* Draft Response
* Optional Report Language
* Workfile Note
* What to Verify
* Risk Flags
* Missing Information

## Required Structured Output

```json
{
  "issue_summary": "",
  "request_explanation": "",
  "recommended_action": "",
  "draft_response": "",
  "optional_report_language": "",
  "workfile_note": "",
  "verification_items": [],
  "risk_flags": [],
  "missing_information": []
}
```

---

# Second Workflow: Workfile Guardian

Build Workfile Guardian as the shared assignment history.

The assignment workfile page must display:

* assignment information
* source documents
* pasted source text
* AI actions
* skill used
* original generated output
* user-edited output
* approved artifacts
* open verification items
* completed verification items
* dates and responsible user

Provide a printable workfile view.

For MVP, browser printing is acceptable. Do not block completion on perfect PDF generation.

---

# Third Workflow: UAD 3.6 Issue Explainer

User can paste a UAD issue, validation-style message, or relevant report text.

Output:

* plain-English explanation
* likely report area
* potential severity
* suggested review steps
* verification items
* workfile note
* caution flags
* missing information

Never call this an official validator.

Use labels such as:

* UAD 3.6 Readiness Review
* UAD Issue Explainer
* Potential Issue
* Pre-Delivery Review

---

# Fourth Workflow: Market Evidence Pack

User uploads an MLS CSV.

Initial deterministic processing must:

* identify probable sale-date column
* identify probable sale-price column
* identify list-price column if available
* identify DOM column if available
* identify property-type column if available
* show the detected mapping
* allow manual correction
* summarize the date range
* summarize sale count
* calculate basic median and average statistics
* identify obvious missing values
* identify possible statistical outliers
* create clean structured data for the skill

The AI skill may create:

* market summary
* observed trend discussion
* caution flags
* report-language draft
* time-adjustment support memo
* workfile evidence note
* verification checklist

The system must not select the appraiser’s final adjustment.

---

# Public Marketing Site

Wire the existing frontend into Django.

Required public pages:

* homepage
* UAD 3.6 Compliance Copilot
* Revision Response Agent
* Market Evidence Pack
* Workfile Guardian
* Skill Library
* UAD 3.6 Readiness Checklist
* Pricing
* Early Access
* login
* signup

Preserve SEO metadata and structured data already present.

The homepage should lead users toward:

* joining early access
* requesting the readiness checklist
* creating an account
* viewing the product workflows

Do not create fake testimonials, customer counts, certifications, lender approvals, or compliance claims.

---

# Application UI

## Logged-in Dashboard

Show:

* recent assignments
* New Assignment button
* New Revision Response shortcut
* open verification items
* recent AI actions
* recent artifacts

## Assignment Page

Show:

* assignment summary
* documents and source material
* available skills
* saved artifacts
* verification checklist
* workfile history

## Skill Run Page

Show:

* short explanation of the skill
* required and optional inputs
* source document selectors
* clear disclaimer
* generate button
* structured results
* edit, copy, approve, and save actions

Use HTMX for:

* generating results
* saving edits
* approving artifacts
* completing verification items
* loading assignment panels

Core content must still be server rendered.

---

# Authentication and Security

Use Django authentication.

Requirements:

* signup
* login
* logout
* password reset if straightforward
* authenticated dashboard
* object-level ownership checks

Every assignment-owned query must be scoped to the logged-in user.

Example:

```python
assignment = get_object_or_404(
    Assignment,
    pk=pk,
    user=request.user,
)
```

Uploaded appraisal documents must never be publicly accessible without permission checks.

Do not expose file paths or confidential source text in logs.

Do not create public assignment-sharing links.

---

# Development Mode

When an API key is not configured and Django is in debug mode:

* use realistic mock structured output
* label it as development mock output
* still create logs, artifacts, and verification items
* allow the complete workflow to be tested

The application must be demonstrable locally without purchasing an API subscription.

---

# Testing

Add meaningful automated tests.

Minimum tests:

* user signup and login
* assignment creation
* assignment ownership
* user cannot access another user’s assignment
* revision form validation
* skill loader reads a valid SKILL.md
* invalid skill metadata is rejected safely
* revision submission creates AIActionLog
* revision submission creates OutputArtifact
* revision submission creates VerificationItem records
* artifact editing preserves original generated content
* artifact approval is saved
* workfile page displays records
* mock LLM mode works without an API key
* uploaded files require authentication and ownership

Do not test exact AI prose.

Test structure, persistence, permissions, and workflow behavior.

---

# Railway Deployment

Create everything needed for Railway deployment.

Required:

* PostgreSQL through `DATABASE_URL`
* Gunicorn
* WhiteNoise
* static file collection
* secure production settings
* `ALLOWED_HOSTS`
* `CSRF_TRUSTED_ORIGINS`
* `.env.example`
* startup command
* migration instructions

Create a simple `Procfile` or Railway start configuration.

Example:

```text
web: gunicorn config.wsgi:application
```

Do not hardcode the project module if the actual module name differs.

Document the exact Railway deployment steps in `README.md`.

---

# Documentation Deliverables

Create or update:

## README.md

Include:

* project description
* stack
* local setup
* environment variables
* migrations
* creating a superuser
* running tests
* Tailwind instructions
* mock AI mode
* Railway deployment
* project structure
* current workflows

## AGENTS.md

Preserve and extend the existing product and coding guidance.

## BUILD_STATUS.md

Track:

* completed work
* current limitations
* next milestone
* known issues
* manual setup requirements

## skills/README.md

Explain:

* skill directory format
* front matter requirements
* output schemas
* adding a new skill
* skill guardrails
* versioning

## tools/README.md

Explain internal deterministic tools and how to add one.

---

# Implementation Phases

Work in this order.

## Phase 1: Inspect and Plan

* inspect existing repo
* identify reusable frontend code
* identify missing backend pieces
* write a concise implementation plan
* do not redesign before understanding the repo

## Phase 2: Django Foundation

* create Django project
* configure PostgreSQL
* configure environment settings
* configure static files
* configure authentication
* create base templates
* move existing frontend into Django templates

## Phase 3: Assignment and Workfile Models

* create models
* create migrations
* register admin
* build assignment list/create/detail views
* enforce ownership permissions

## Phase 4: Skill Loader

* create skill Markdown structure
* implement YAML and Markdown loader
* add validation
* expose active skills to the UI
* add tests

## Phase 5: Revision Response Agent

* create form and HTMX workflow
* connect LLM or mock provider
* save logs and artifacts
* create verification items
* build edit/approve/copy interactions
* display output in structured cards

## Phase 6: Workfile Guardian

* build complete assignment history
* show sources, actions, artifacts, and verification
* add printable export

## Phase 7: UAD Issue Explainer

* create skill file
* create form and workflow
* save outputs to workfile
* include correct disclaimers

## Phase 8: Market Evidence Pack

* implement CSV upload
* implement column detection and mapping
* calculate deterministic statistics
* run market-evidence skill
* save evidence artifact

## Phase 9: Production Readiness

* security review
* error handling
* responsive UI review
* test suite
* Railway deployment files
* documentation
* sitemap and SEO verification

---

# Definition of Done

The first build is complete only when all of the following are true:

* the existing marketing design is preserved inside Django
* a new user can sign up and sign in
* the user can create an assignment
* the user can run the Revision Response skill
* a real or mock structured response is generated
* inputs and outputs are persisted
* verification items are created
* the user can edit and approve an artifact
* the workfile displays the complete history
* users cannot access each other’s assignments or documents
* the skill instructions come from SKILL.md files
* the app runs locally from documented commands
* automated tests pass
* the app is configured for Railway and PostgreSQL
* README and build status documentation are complete
* the site works well on mobile and desktop

Do not declare completion while only the UI exists.

Do not declare completion while outputs are not saved.

Do not declare completion while ownership permissions are missing.

Do not declare completion while the Revision Response workflow is incomplete.

---

# Working Method for Codex

Proceed autonomously through the phases.

Before coding:

1. Inspect the repo.
2. Summarize the current state.
3. State the implementation sequence.
4. Identify any true blockers.

Do not ask questions for decisions that can be reasonably inferred from this document or the existing repo.

After each phase:

1. run relevant tests
2. inspect errors
3. fix failures
4. update `BUILD_STATUS.md`
5. summarize what changed

Favor working software over speculative architecture.

When choosing between a larger abstraction and a smaller explicit implementation, choose the smaller implementation unless there is a demonstrated need.

The first priority is a complete Revision Response Agent and traceable Workfile Guardian running inside the existing CoAppraiser design.

```

The most important part is the **Definition of Done**. Without it, Codex may create models, templates, and placeholder services and then report that the project is finished. This goal forces one complete workflow from account creation through approved workfile artifact.
```
