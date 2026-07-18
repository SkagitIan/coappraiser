COAPPRAISER SYNTHETIC DEMONSTRATION PACKAGE

Scenario: 02_reconcile
Identifier: SYNTHETIC-SUBJECT-001
Purpose: The same-subject package contains intentional data, narrative, support, and photo conflicts.
XML status: included

CONTROLLED DATA NOTICE
This is a synthetic appraisal package: every assignment fact, identifier, report
statement, comparable, and conclusion is fictional. It contains no borrower,
client, lender, appraiser, signature, credential, address, or value opinion.
The residential photographs are owner-supplied reference images, selected to
exclude visible addresses, signs, vehicles, people, and personal portraits, then
re-encoded without EXIF metadata. They are not evidence from a real assignment.
Appraiser judgment is required.

DELIBERATE SCENARIO CONDITIONS
- XML condition C4 conflicts with PDF condition C3.
- Structured XML condition C4 conflicts with narrative condition C3.
- Structured XML quality Q3 conflicts with narrative quality Q4.
- Three comparables are identified, but only one has commentary.
- The PDF says there is no rear deck or accessory enclosure, while the rear photos visibly show both.
- The PDF describes complete exterior cladding, while a rear photo visibly shows an unfinished enclosure wall.

EXPECTED FINDING TYPES
- Warning to reconcile condition between XML and PDF.
- Warning to reconcile structured and narrative condition.
- Warning to reconcile structured and narrative quality.
- Warning to review incomplete comparable commentary.
- A GPT-5.6 visual review prompt may identify the deck/enclosure and exterior-description conflicts using exact photo filenames.

GPT-5.6 OUTPUT
GPT-5.6 output may vary slightly in wording, prioritization, or additional
evidence-grounded interpretive findings. Preflight evidence-review findings appear
separately from deterministic findings. The deterministic outcome listed above is designed
to remain predictable.
