# How CoAppraiser is evaluated

This document explains, in plain language, how we test CoAppraiser Preflight,
what the tests currently prove, what went wrong during testing, and what we
changed in response.

## The short version

CoAppraiser has three different kinds of tests:

1. **Normal software tests** make sure accounts, uploads, findings, decisions,
   workfile records, privacy boundaries, and model failures behave correctly.
2. **UAD and report comparison tests** make sure CoAppraiser can read supported
   information from real UAD 3.6 sample files and identify deliberately created
   PDF/XML conflicts.
3. **Live GPT-5.6 tests** send controlled appraisal packages through the real
   OpenAI Responses API several times. These tests check whether GPT-5.6 finds
   the intended issue, avoids inventing issues in a clean package, cites its
   evidence, respects professional boundaries, and returns usable structured
   results.

The current verified results are:

| Test group | Current result |
| --- | --- |
| Django application tests | 59 of 59 pass |
| Official UAD sample scenarios | 12 of 12 pass |
| Controlled PDF/XML conflict cases | 4 of 4 pass |
| Clean GPT-5.6 package | 3 of 3 runs returned no GPT finding |
| Comparable-commentary GPT-5.6 package | 3 of 3 runs found the intended issue |
| Visual-conflict GPT-5.6 package | 3 of 3 final affected-case runs found the intended issue |
| Missing citations or appraiser-judgment language | 0 |
| Professional-boundary violations | 0 |

These are engineering test results. They are not a claim that CoAppraiser is an
official UAD validator, that every appraisal issue will be detected, or that a
report will be accepted by a client or GSE.

## Why we built this evaluation system

An AI review can look impressive while still being inconsistent. A good answer
once is not enough. We needed to know:

- Can CoAppraiser read real UAD 3.6 file structures?
- Does it find a known conflict without adding unrelated findings?
- Does it stay quiet when the supplied package is internally consistent?
- Can a finding be traced to an exact field, report page, or photograph?
- Does the model avoid determining value, prescribing adjustments, selecting
  comparables, declaring compliance, or guaranteeing acceptance?
- What happens when OpenAI is unavailable or returns an unusable response?
- Can another developer reproduce the same tests?

The evaluation stack was built to answer those questions separately. Fixed
rules are not graded as if they were AI, and GPT-5.6 is not given credit for a
conflict that a repeatable rule already found.

## Test 1: application and safety behavior

The Django test suite covers the complete product workflow, including:

- account ownership and user-scoped reviews;
- public-demo session isolation;
- ZIP safety and supported-file intake;
- XML, PDF, image, and package handling;
- deterministic findings and GPT-generated evidence findings;
- visual-source filename verification;
- duplicate-finding suppression;
- resolved, deferred, not-applicable, and open decisions;
- decision notes and workfile export;
- preservation of uploaded packages when the model fails;
- rejection of mock AI in production;
- professional-boundary filtering;
- Responses API request construction;
- public messaging and demo behavior.

Run it with:

```powershell
python manage.py test
```

The expected result is currently **59 passing tests**.

Some tests intentionally simulate provider failures. Their error messages may
appear in test output even when the suite passes. That is expected: the test is
confirming that the package and deterministic findings survive the failure.

## Test 2: official UAD 3.6 sample coverage

We use Fannie Mae's Appendix D-1 sample archive as a local evaluation corpus.
It contains 12 professional sample scenarios with paired rendered PDFs and UAD
XML files.

The publisher files are not committed to this repository. Each developer must
download the archive from Fannie Mae and import it locally. CoAppraiser records
the archive hash so developers can confirm that they tested the same bytes.

For every scenario, the current gate requires CoAppraiser to find:

- the subject address;
- overall condition;
- overall quality;
- above-grade finished area;
- the exact XML source path;
- the matching value and page location in the rendered PDF.

Run it with:

```powershell
python manage.py evaluate_uad_corpus --strict
```

The current result is **12 of 12 scenarios passing**.

This proves limited, measured normalization coverage for those supported
fields. It does not mean CoAppraiser implements every UAD field or performs
official UAD validation.

## Test 3: controlled PDF/XML conflicts

The next gate starts with a local copy of an official sample and changes one
fact at a time. The original publisher file is never modified.

The four cases are:

1. a clean baseline that should produce no cross-source conflict;
2. a condition mismatch;
3. a quality mismatch;
4. an above-grade finished-area mismatch.

Each changed case must produce exactly the expected rule. An unexpected extra
rule fails the test.

Run it with:

```powershell
python manage.py evaluate_uad_regressions --strict
```

The current result is **4 of 4 cases passing**.

## Test 4: live GPT-5.6 behavior

The live evaluation uses three controlled ZIP packages:

### Aligned package

The XML, rendered report, commentary, and photographs tell the same disclosed
story. GPT-5.6 should not invent an additional inconsistency.

Expected result: **zero GPT findings**.

### Visual-conflict package

The report says no rear deck, covered patio, or accessory enclosure was
observed. The selected rear photographs show those features. The package also
contains repeatable XML/PDF conflicts that are handled separately by
deterministic rules.

Expected result: **one or two cited visual findings**, depending on whether
GPT-5.6 groups the deck, enclosure, and exterior-finish evidence together.

### Incomplete-comparable-commentary package

The rendered report shows three comparables, but only one receives individual
commentary. Its photographs and condition disclosure are otherwise aligned so
the case does not accidentally test a second visual conflict.

Expected result: **one comparable-commentary finding**.

For every accepted finding, the scorer checks:

- expected and unexpected finding topics;
- maximum reviewed finding count;
- source location;
- supporting evidence;
- appraiser-judgment language;
- prohibited professional conclusions;
- model response ID;
- returned model name;
- latency;
- input, output, reasoning, and total tokens.

The live evaluator never falls back to mock AI. It uses temporary users, a
temporary local database, and temporary local file storage. Railway supplies
only the model credentials.

Run one paid pass with:

```powershell
.\scripts\run_evals.ps1 -Live -Repeat 1
```

Run the release gate with:

```powershell
.\scripts\run_evals.ps1 -Live -Repeat 3
```

These commands incur OpenAI API usage.

## What we learned from the repeated runs

The first three-run baseline produced six strict passes out of nine. Human
review showed two different problems:

1. One visual run returned both visual conflicts deliberately placed in the
   package. The evaluator incorrectly allowed only one finding. The reviewed
   maximum was corrected to two.
2. The comparable-commentary issue was found only once in three runs. That was
   a genuine recall problem.

We added a general instruction telling the reviewer to compare applicable
comparable-grid facts with individual commentary. We did not tell the model the
fixture answer or require it to produce a finding.

That targeted case then reached three of three, but the next full run exposed
problems in the fixtures themselves:

- The package labeled "aligned" showed the same condition relationship for
  three comparables while only one comment acknowledged it.
- The package intended to isolate comparable commentary also contained a
  separate defect-summary/photo inconsistency.
- A shared commentary template sometimes said two condition ratings differed
  when the generated grid showed that they were the same.

GPT-5.6 was correct to flag these relationships. Weakening the scorer would
have hidden bad test data, so we corrected the fixtures instead.

We then found two evaluation-code problems:

- A commentary finding that cited a rendered PDF was mislabeled as a visual
  condition finding. The scorer now prefers the specific meaning of the finding
  over the input format.
- Any rendered PDF citation could bypass deterministic duplicate suppression.
  Now only an actual appraisal photograph can justify keeping a distinct visual
  finding when a deterministic finding covers the same topic.

Finally, GPT-5.6 returned empty or malformed structured output during two live
runs. CoAppraiser now makes one bounded retry for that specific condition,
records the attempt count, and returns a useful failure if the second response
is also unusable. The evaluator continues after operational failures and
records them as failed runs.

## Why the final evidence uses an affected-case rerun

After the corrected full regression:

- the aligned package passed three of three;
- the comparable-commentary package passed three of three;
- the visual issue was detected in all three visual runs, but one run also
  found a real grid/commentary error created by the shared fixture generator.

The generator was corrected. Hash comparison confirmed that the aligned and
comparable packages did not change; only the visual package changed. Under the
documented protocol, only the affected visual case needed to be rerun. Its final
result was three of three.

We therefore do not describe this as one final monolithic nine-of-nine report.
The release evidence is the unchanged cases' three-of-three full-regression
results plus the changed visual case's final three-of-three targeted result.
Future changes to the shared prompt, scorer, model settings, or intake path
require a new complete nine-run gate.

## Structured-output and operational safeguards

The production model path:

- uses the OpenAI Responses API exclusively;
- requires strict structured JSON;
- records the response ID, model, usage, and number of attempts;
- retries invalid structured output once;
- never silently substitutes mock output;
- preserves the package and deterministic findings if the model still fails;
- rejects incomplete, low-confidence, or professionally prohibited findings.

The evaluator now writes:

- `gpt56-demo-evaluation.json`, the convenient latest result;
- a timestamped report that preserves the individual run;
- the evaluated case IDs;
- a SHA-256 hash of the case specification;
- a SHA-256 hash of the system prompt.

Generated reports remain under `.eval-data/reports/` and are ignored by Git.

## The locked release protocol

1. Run the complete no-cost stack:

   ```powershell
   .\scripts\run_evals.ps1 -Full
   ```

   All Django tests, all 12 official scenarios, and all four deterministic
   regression cases must pass.

2. If the prompt, model settings, scorer, multimodal intake, or another shared
   review path changes, run:

   ```powershell
   .\scripts\run_evals.ps1 -Live -Repeat 3
   ```

3. The aligned case must remain three of three with zero findings. Each seeded
   issue must be detected three of three.

4. Every accepted finding must contain a source, evidence, and
   appraiser-judgment language. Professional-boundary violations must remain
   zero.

5. Operational failures count as failures. They are not removed from the score.

6. If only one fixture changes, confirm the other package hashes are unchanged
   and rerun the affected case three times. A shared generator change requires
   every affected case.

7. Never lower a threshold after seeing a failed result. A human label
   correction needs a written reason and an affected-case rerun.

8. For now, 100 seconds and 20,000 total tokens are monitoring alerts, not
   release failures. More runs are needed before latency or token limits become
   statistical quality claims.

## Files that make up the evaluation system

| File or directory | Plain-English purpose |
| --- | --- |
| `scripts/run_evals.ps1` | One command for the no-cost gates, full tests, and optional paid GPT runs. |
| `evals/README.md` | Short operator instructions. |
| `evals/QUALITY_GATES.md` | Exact pass/fail rules and the recorded evaluation history. |
| `evals/cases/gpt56_demo.json` | Expected outcomes for the three live GPT packages. |
| `evals/cases/uad36_cross_source.json` | Expected outcomes for controlled PDF/XML mutations. |
| `evals/sources/uad_d1.json` | Publisher information and the expected official archive hash. |
| `apps/preflight/uad36.py` | Reads the official UAD sample structure and retains exact source paths. |
| `apps/preflight/evaluation.py` | Scores GPT findings without changing application data. |
| `apps/preflight/management/commands/import_uad_eval_corpus.py` | Safely imports the locally downloaded official archive. |
| `apps/preflight/management/commands/evaluate_uad_corpus.py` | Runs the 12-scenario UAD coverage gate. |
| `apps/preflight/management/commands/evaluate_uad_regressions.py` | Runs the four controlled conflict cases. |
| `apps/preflight/management/commands/evaluate_gpt56.py` | Runs paid isolated GPT cases and writes auditable reports. |
| `scripts/run_isolated_gpt_eval.py` | Uses Railway model credentials without using production data or storage. |
| `apps/preflight/ai_review.py` | Defines the bounded reviewer instructions and validates accepted findings. |
| `apps/preflight/llm_client.py` | Calls GPT-5.6 through the Responses API and handles structured-output failures. |
| `demo/build_scenario_packages.py` | Rebuilds the three deterministic synthetic packages. |
| `demo/coappraiser-demo-*.zip` | The three controlled packages used by the live evaluator and public demo. |
| `apps/preflight/tests.py` and `apps/preflight/test_demo.py` | Automated workflow, safety, model-request, and demo regression tests. |

## What these tests do not prove

The current evaluation does not prove:

- complete UAD 3.6 field coverage;
- official Fannie Mae, Freddie Mac, lender, AMC, or GSE validation;
- USPAP compliance;
- appraisal correctness;
- reliable detection of every possible narrative or photographic issue;
- a statistically established production success rate;
- a property-condition diagnosis from photographs.

GPT-5.6 findings remain review prompts. The appraiser verifies the evidence,
makes every appraisal decision, and records what was resolved, deferred, left
open, or found not applicable.

## Sensible next expansion

The current protocol is sufficient for the Build Week demonstration. The next
evaluation work should remain narrow:

1. add an automated provider-timeout recovery test;
2. add one human-reviewed visual scenario at a time;
3. preserve a larger history of repeated runs before publishing reliability,
   latency, or cost claims;
4. expand UAD field coverage only when exact official sample paths and expected
   report representations have been verified.
