# Build Week Preflight demo package

`coappraiser-build-week-demo.zip` is a controlled, entirely synthetic appraisal package. It contains no borrower, client, lender, appraiser, or real-property information. The source files are retained in `preflight_build_week/` so the package can be audited before a demonstration.

Upload the ZIP through **Preflight > New review**. The deterministic rules produce these stable findings even if GPT wording varies:

- XML condition `C4` conflicts with PDF condition `C3`.
- Structured condition `C4` conflicts with narrative condition `C3`.
- Structured quality `Q3` conflicts with narrative quality `Q4`.
- Three comparables are identified, but only one has commentary.

GPT-5.6 may add evidence-grounded interpretive findings. Its output is deliberately shown separately from deterministic checks.

To rebuild the ZIP after intentionally changing a source file, run from the repository root:

```powershell
Compress-Archive -Path demo\preflight_build_week\* -DestinationPath demo\coappraiser-build-week-demo.zip -Force
```

The included PDF and image fixtures are synthetic test artifacts, not a real appraisal report.
