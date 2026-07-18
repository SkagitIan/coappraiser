# CoAppraiser evaluation corpus

This directory contains code and metadata for evaluations, not appraisal files.
Downloaded corpora and generated cases belong under `.eval-data/`, which Git
ignores.

## Run the evaluations yourself

From PowerShell in the repository root, the shortest no-cost command is:

```powershell
.\scripts\run_evals.ps1
```

It runs the official-sample normalization gate and controlled cross-source
regressions. It does not call OpenAI.

Add the Django system check and full test suite:

```powershell
.\scripts\run_evals.ps1 -Full
```

Run one paid pass of all three GPT-5.6 cases using linked Railway credentials
while forcing a local temporary database and file store:

```powershell
.\scripts\run_evals.ps1 -Live -Repeat 1
```

Run only the visual case:

```powershell
.\scripts\run_evals.ps1 -Live -Repeat 1 -Case visual-condition-evidence
```

For a release-quality sample, use `-Repeat 3`. Live runs incur OpenAI usage and
can take several minutes. A nonzero exit code means at least one gate failed.
Machine-readable results are written to `.eval-data/reports/`.

If Windows blocks local PowerShell scripts, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_evals.ps1
```

If `.eval-data/uad-d1/` does not exist yet, import the archive once:

```powershell
python manage.py import_uad_eval_corpus ".\downloads\Appendix D-1 URAR Sample Use Cases and XML Files_0.zip"
```

## Import the official UAD sample archive

1. Visit the [Fannie Mae UAD page](https://singlefamily.fanniemae.com/delivering/uniform-mortgage-data-program/uniform-appraisal-dataset).
2. In **Documentation**, download **Appendix D-1: URAR Sample Scenarios and XML
   Files**. Review and accept the publisher's terms yourself.
3. Run:

   ```powershell
   python manage.py import_uad_eval_corpus "C:\path\to\the-downloaded.zip"
   ```

The command validates the ZIP, extracts it beneath `.eval-data/uad-d1/`, and
writes `manifest.json` with file hashes, candidate PDF/XML pairs, and an XML
structure profile. It never runs an AI review or modifies application data.

Use `--inventory-only` to inspect the archive without extracting it:

```powershell
python manage.py import_uad_eval_corpus "C:\path\to\the-downloaded.zip" --inventory-only
```

Measure the currently supported normalization fields across every imported
scenario:

```powershell
python manage.py evaluate_uad_corpus --strict
python manage.py evaluate_uad_regressions --strict
```

This writes a machine-readable report beneath `.eval-data/reports/`. The strict
gate requires a subject address, overall condition, overall quality, and
above-grade finished area in every XML and requires those values to agree with
the paired rendered PDF. PDF evidence retains its page number.

The regression gate applies controlled condition, quality, and above-grade area
mutations to a local copy of the official SF5 XML while retaining its paired PDF.
Each case must return exactly the expected cross-source rule; the clean case must
return none. Only the mutation recipes and expected rules are committed.

## Live GPT-5.6 evaluation

With the production model variables and a deliberate paid-call confirmation:

```powershell
python manage.py evaluate_gpt56 --repeat 3 --confirm-paid-api --strict
```

The runner never falls back to mock AI. It scores required and unexpected
finding topics, source citations, appraiser-judgment language, professional
boundary violations, latency, and token usage. It uses temporary users and media
and removes them after each run. Reports remain under `.eval-data/reports/`.

When the API key exists only in the linked Railway service, use the isolated
launcher. It imports the model credentials but replaces `DATABASE_URL` with the
local SQLite database; the evaluator itself replaces storage with a temporary
filesystem:

```powershell
railway run python scripts/run_isolated_gpt_eval.py --repeat 3 --confirm-paid-api --strict
```

## Why the archive is not in Git

The samples are published for UAD implementation work, but CoAppraiser does not
assume permission to redistribute them. Each developer obtains the archive from
the authoritative publisher. The local manifest records source and SHA-256 so a
team can confirm that it evaluated the same bytes.

An official sample is a representation baseline, not proof that Preflight should
return zero findings. Expected findings must be reviewed and labeled by a
qualified human before they become release gates.
