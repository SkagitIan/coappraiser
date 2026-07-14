# Preflight domain model

`PreflightReview` -> many immutable `ReviewVersion` records -> many `ReviewFile` records and `ReviewFinding` records. Each finding has one `FindingDecision`. A review has one generated `WorkfileReviewRecord`. Ownership is inherited from the review user and enforced in every view.
