# CoAppraiser professional product roadmap

CoAppraiser's next stage is not more surface area. It is a dependable Preflight
pipeline that can read real appraisal packages, point to the evidence behind each
finding, and demonstrate its quality with repeatable evaluations.

## Product goals

### 1. Trustworthy UAD 3.6 intake

Accept a normal package from appraisal software, identify its XML, rendered
report, and photographs, and preserve the source location of every extracted
fact. Unsupported or unreadable material must be reported clearly rather than
silently ignored.

**Release gate:** the supported fields in each official sample XML can be
normalized into CoAppraiser observations and traced back to their source paths.

### 2. Measurable review quality

Use official paired PDF/XML samples as a stable baseline, then create controlled
copies with one deliberate inconsistency at a time. Measure whether deterministic
rules and GPT-5.6 find the seeded issue, cite the right evidence, and avoid
unrelated claims.

**Release gate:** every supported review rule has at least one positive case and
one clean case; evaluation reports show detection, citation, and false-positive
results separately.

### 3. Reliable production operation

Every review must preserve the uploaded package and deterministic results even if
the model is slow or unavailable. Processing state, model identity, errors, and
the final appraiser decision must remain visible and auditable.

**Release gate:** upload, review, decision, and workfile export pass desktop and
mobile smoke tests; provider failures have a tested recovery path.

### 4. Professional boundaries and data handling

CoAppraiser identifies evidence for professional review. It does not determine
value, select adjustments, declare compliance, or guarantee acceptance. Official
samples and private appraisal packages are not committed to this repository.

**Release gate:** privacy, storage, retention, model-input, and deletion behavior
are documented and verified against production configuration.

## Delivery milestones

1. **Evaluation foundation (current):** safe local official-sample importer,
   archive manifest, UAD XML structure inspection, and unit tests.
2. **Real UAD normalization:** map a deliberately limited set of high-value UAD
   3.6 fields from the imported samples and retain exact XML paths.
3. **Controlled cases:** build local mutations for condition, quality, GLA,
   narrative support, and photo-to-report inconsistencies.
4. **Scoring:** add a repeatable runner and machine-readable report for detection,
   source citation, severity, prohibited claims, and false positives.
5. **Release qualification:** establish thresholds, regression tests, operational
   smoke tests, and a reviewed limitations matrix.

## Current definition of done

The first milestone is complete when a developer can download Appendix D-1 from
Fannie Mae, import it without committing the source files, see an inventory of
the PDF/XML pairs and XML structures, and reproduce the importer tests locally.

