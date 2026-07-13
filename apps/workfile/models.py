from django.db import models
from apps.assignments.models import Assignment
from apps.ai_tools.models import AIActionLog

class OutputArtifact(models.Model):
    ARTIFACT_TYPES = [(x, x.replace("_", " ").title()) for x in ["revision_response", "report_language", "workfile_note", "support_checklist", "uad_issue_summary", "market_evidence_memo", "qa_punch_list"]]
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="artifacts")
    title = models.CharField(max_length=200)
    artifact_type = models.CharField(max_length=50, choices=ARTIFACT_TYPES)
    source_action = models.ForeignKey(AIActionLog, on_delete=models.SET_NULL, null=True, blank=True, related_name="artifacts")
    original_generated_content = models.JSONField(default=dict)
    user_edited_content = models.JSONField(default=dict)
    approval_status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("approved", "Approved")], default="draft")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class VerificationItem(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("verified", "Verified"), ("needs_more_info", "Needs more information"), ("not_applicable", "Not applicable")]
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="verification_items")
    artifact = models.ForeignKey(OutputArtifact, on_delete=models.CASCADE, null=True, blank=True, related_name="verification_items")
    description = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="open")
    user_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

