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

### Repeated baseline: July 18, 2026

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

These measurements are a baseline, not a public reliability claim.

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

## Next gates

1. Add one general review-protocol instruction requiring the model to examine
   applicable comparable-grid facts against the supplied commentary. Do not
   mention a fixture answer or force a finding.
2. Run the comparable case three times. It must pass 3/3 before another full
   run is justified.
3. Rerun all three cases three times after that prompt change. Lock only if:
   the aligned case is 3/3 clean; each seeded topic is detected 3/3; every
   accepted finding has citations and judgment language; there are zero
   boundary violations; and finding counts remain within reviewed case labels.
4. Treat 100 seconds and 20,000 total tokens as provisional monitoring alerts,
   not release failures, until more runs establish stable distributions.
5. Add provider-timeout recovery to the automated suite before treating the
   operational protocol as complete.
