# CoAppraiser evaluation corpus

This directory contains code and metadata for evaluations, not appraisal files.
Downloaded corpora and generated cases belong under `.eval-data/`, which Git
ignores.

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

## Why the archive is not in Git

The samples are published for UAD implementation work, but CoAppraiser does not
assume permission to redistribute them. Each developer obtains the archive from
the authoritative publisher. The local manifest records source and SHA-256 so a
team can confirm that it evaluated the same bytes.

An official sample is a representation baseline, not proof that Preflight should
return zero findings. Expected findings must be reviewed and labeled by a
qualified human before they become release gates.
