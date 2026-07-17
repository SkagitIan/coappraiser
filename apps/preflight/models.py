from django.conf import settings
from django.db import models


class PreflightReview(models.Model):
    STATUS_CHOICES = [(x, x.replace("_", " ").title()) for x in ["draft", "processing", "completed", "failed"]]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preflight_reviews")
    title = models.CharField(max_length=200)
    subject_identifier = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def open_findings(self):
        return self.findings.exclude(decision__status__in=["resolved", "not_applicable"]).count()


class ReviewVersion(models.Model):
    STATUS_CHOICES = [(x, x.replace("_", " ").title()) for x in ["uploaded", "validated", "parsed", "reviewed", "completed", "failed"]]
    review = models.ForeignKey(PreflightReview, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="uploaded")
    package_hash = models.CharField(max_length=64, blank=True)
    parser_version = models.CharField(max_length=30, default="preflight-1")
    rule_version = models.CharField(max_length=30, default="rules-1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["review", "number"], name="unique_preflight_version")]
        ordering = ["-number"]


class ReviewFile(models.Model):
    KIND_CHOICES = [(x, x.upper()) for x in ["xml", "pdf", "image", "ssr", "other"]]
    version = models.ForeignKey(ReviewVersion, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="preflight/%Y/%m/")
    original_name = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="other")
    sha256 = models.CharField(max_length=64)
    extracted_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class ExtractedObservation(models.Model):
    SOURCE_CHOICES = [(x, x.upper()) for x in ["xml", "pdf", "image", "ssr", "other"]]
    version = models.ForeignKey(ReviewVersion, on_delete=models.CASCADE, related_name="observations")
    source_file = models.ForeignKey(ReviewFile, on_delete=models.CASCADE, related_name="observations", null=True, blank=True)
    field_code = models.CharField(max_length=100)
    value = models.TextField(blank=True)
    normalized_value = models.CharField(max_length=255, blank=True)
    source_kind = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_location = models.CharField(max_length=300, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class AIExecution(models.Model):
    STATUS_CHOICES = [(x, x.title()) for x in ["running", "completed", "failed", "skipped"]]
    version = models.ForeignKey(ReviewVersion, on_delete=models.CASCADE, related_name="ai_executions")
    operation = models.CharField(max_length=80)
    provider = models.CharField(max_length=50, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    prompt_version = models.CharField(max_length=30, default="preflight-ai-1")
    system_prompt = models.TextField(blank=True)
    input_snapshot = models.JSONField(default=dict)
    raw_response = models.TextField(blank=True)
    parsed_response = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class ReviewFinding(models.Model):
    SEVERITIES = [(x, x.title()) for x in ["critical", "warning", "advisory"]]
    CATEGORIES = [(x, x.replace("_", " ").title()) for x in ["fix_before_delivery", "judgment_review", "cleanup"]]
    review = models.ForeignKey(PreflightReview, on_delete=models.CASCADE, related_name="findings")
    version = models.ForeignKey(ReviewVersion, on_delete=models.CASCADE, related_name="findings")
    rule_code = models.CharField(max_length=80)
    signature = models.CharField(max_length=180)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    severity = models.CharField(max_length=20, choices=SEVERITIES)
    observed = models.TextField()
    location = models.CharField(max_length=300, blank=True)
    why_it_matters = models.TextField()
    recommended_action = models.TextField()
    evidence = models.JSONField(default=list)
    guidance = models.JSONField(default=list)
    basis = models.CharField(max_length=30, default="deterministic")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["severity", "-created_at"]


class FindingDecision(models.Model):
    STATUS_CHOICES = [(x, x.replace("_", " ").title()) for x in ["open", "resolved", "deferred", "not_applicable"]]
    finding = models.OneToOneField(ReviewFinding, on_delete=models.CASCADE, related_name="decision")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    note = models.TextField(blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decided_at = models.DateTimeField(auto_now=True)


class WorkfileReviewRecord(models.Model):
    review = models.OneToOneField(PreflightReview, on_delete=models.CASCADE, related_name="workfile_record")
    snapshot = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)

