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

Current smoke result: each case has passed one isolated live GPT-5.6 run. This
proves the execution path and reviewed labels, but is not yet a statistically
meaningful pass-rate claim.

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

- collect at least three live repetitions per GPT case and set empirical
  pass-rate, latency, and token thresholds;
- expand human-reviewed labels before adding more visual scenarios;
- add operational recovery tests for provider timeouts.
