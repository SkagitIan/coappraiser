# CoAppraiser quality gates

These gates define what the repository currently proves. They do not claim
official UAD validation, USPAP compliance, appraisal correctness, or GSE
acceptance.

## Authoritative corpus

- Publisher: Fannie Mae
- Corpus: Appendix D-1, URAR Sample Scenarios and XML Files
- Reviewed archive SHA-256:
  `9aa50fa479fc6bfd77694298c62947e112854a8c64fb05c8e81f77999df43b19`
- Contents observed: 12 scenario ZIPs, 12 XML files, 13 PDFs, and 12 paired
  scenario PDF/XML reports
- Publisher files are local-only and ignored by Git.

## Gate 1: real UAD normalization and representation agreement

```powershell
python manage.py evaluate_uad_corpus --strict
```

Required for every official scenario:

- subject address, including a separately encoded unit when present;
- overall condition;
- overall quality;
- standard above-grade finished area;
- exact source XML paths;
- matching values in the paired rendered PDF;
- PDF page location retained for the matched evidence.

Current measured result: **12/12 scenarios pass**.

## Gate 2: controlled cross-source regressions

```powershell
python manage.py evaluate_uad_regressions --strict
```

The committed recipes modify local copies only. The clean case must produce no
cross-source finding. Each single-field mutation must produce exactly its
expected rule and no unrelated cross-source rule.

Current measured result: **4/4 cases pass**:

- clean SF5 baseline;
- condition conflict;
- quality conflict;
- above-grade finished-area conflict.

## Gate 3: professional boundaries

The automated Django tests require:

- appraiser decisions remain separate persisted records;
- every accepted GPT finding states that appraiser judgment is required;
- valuation directives, final adjustments, comparable-selection directions,
  compliance declarations, and acceptance guarantees are suppressed;
- low-confidence and evidence-incomplete model findings are not displayed;
- deterministic findings survive a model failure.

## Gate 4: bounded GPT-5.6 behavior

The paid runner uses three controlled packages:

- an aligned package expected to produce no GPT finding;
- a report-to-photo conflict expected to produce one cited visual finding;
- incomplete comparable commentary expected to produce one cited commentary
  finding.

Each run rejects unexpected topics, missing citations, missing
appraiser-judgment language, professional-boundary violations, and excess
findings. It also records the response ID, returned model, latency, and token
usage.

### Repeated baseline and protocol refinement: July 18, 2026

Three isolated live runs per case produced:

| Case | Detection result | Original strict result | Review |
| --- | --- | --- | --- |
| Aligned package | 3/3 returned no GPT finding | 3/3 | Correct negative behavior. |
| Visual report conflict | 3/3 detected cited visual conflicts | 2/3 | One run returned both deliberately seeded visual conflicts; the original one-finding maximum was incorrect and is now two. |
| Incomplete comparable commentary | 1/3 detected the required gap | 1/3 | Recall is not reliable enough to lock. |

The unadjusted report recorded **6/9 strict passes**. Human review found the
visual failure was a label-definition error rather than a bad model result.
Comparable-commentary recall remains a genuine model/prompt failure.

Across the nine calls:

- every accepted finding included a source location and supporting evidence;
- every accepted finding included appraiser-judgment language;
- no accepted finding violated a professional boundary;
- average latency was 52.5 seconds, with an observed range of 15.5 to 80.2
  seconds;
- average total usage was 14,615 tokens, with an observed range of 12,305 to
  16,007 tokens;
- the API returned `gpt-5.6-sol` for all recorded calls.

Protocol refinement then:

- added a general comparable-grid-to-commentary review step without supplying
  a fixture answer;
- corrected the aligned fixture so every reported condition relationship is
  actually reconciled;
- corrected the incomplete-commentary fixture so it isolates that gap without
  an unrelated visual contradiction;
- corrected semantic scoring so a rendered PDF citation does not turn a
  commentary finding into a visual-condition topic;
- limited deterministic-duplicate bypass to findings supported by an actual
  appraisal photo, not merely the rendered PDF;
- added one bounded retry for empty or invalid structured output and made the
  evaluator preserve operational failures in its report.

Final affected-case evidence:

- aligned package: **3/3 clean** in the corrected full regression;
- incomplete comparable commentary: **3/3 detected** in the corrected full
  regression;
- visual conflict: **3/3 detected** after the visual fixture's final
  grid/commentary correction;
- every accepted finding in these gates retained citations and
  appraiser-judgment language, with zero professional-boundary violations.

The aligned and incomplete package hashes did not change during the final
visual-only correction, so only the affected visual case was rerun. These are
engineering release gates, not a public statistical reliability claim.

## Reproducing the evidence

```powershell
python manage.py import_uad_eval_corpus "downloads\Appendix D-1 URAR Sample Use Cases and XML Files_0.zip"
python manage.py evaluate_uad_corpus --strict
python manage.py evaluate_uad_regressions --strict
python manage.py test
```

Machine-readable reports are written to `.eval-data/reports/`.

The PowerShell wrapper runs the same gates:

```powershell
.\scripts\run_evals.ps1 -Full
.\scripts\run_evals.ps1 -Live -Repeat 3
```

## Locked release protocol

1. Run `.\scripts\run_evals.ps1 -Full`. All Django tests, all 12 official
   scenarios, and all four deterministic regressions must pass.
2. When the prompt, model settings, scorer, or shared intake path changes, run
   `.\scripts\run_evals.ps1 -Live -Repeat 3`. The aligned case must remain
   3/3 clean and each seeded topic must be detected 3/3.
3. When only one fixture changes, verify unchanged package hashes and run that
   case three times. A shared generator change requires all affected cases.
4. Every accepted finding must have a source location, supporting evidence,
   appraiser-judgment language, and zero professional-boundary violations.
5. Operational failures count as failed runs. The evaluator must continue and
   preserve them in the timestamped report; they are never silently retried
   beyond the single bounded structured-output retry.
6. Do not weaken a case threshold after a run. Human label corrections require
   a written rationale and a rerun of every affected case.
7. Treat 100 seconds and 20,000 total tokens as provisional monitoring alerts,
   not release failures, until more runs establish stable distributions.

## Next expansion

- add a controlled provider-timeout test;
- add more human-reviewed visual scenarios one at a time;
- collect more repeated runs before making any public reliability claim.
