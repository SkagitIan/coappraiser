---
name: Market Evidence Pack
slug: market-evidence
category: market-evidence
version: 1.0.0
status: active
description: Turn appraiser-provided sales data into cautious market evidence observations.
input_types:
  - mls_csv
  - effective_date
  - appraiser_notes
output_types:
  - market_summary
  - trend_observations
  - caution_flags
  - report_language
  - workfile_note
  - verification_items
---

# Guardrails
Describe the provided data only. Never select a final adjustment, determine value, or imply the data proves applicability to the subject or selected comparables.

# Procedure
Summarize the deterministic statistics, identify observations and limitations, draft cautious language, and list what the appraiser should verify.

