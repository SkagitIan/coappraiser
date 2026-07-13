from django.conf import settings
from django.db import models

class Assignment(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("complete", "Complete"), ("archived", "Archived")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    property_address = models.CharField(max_length=300, blank=True)
    assignment_type = models.CharField(max_length=100, blank=True)
    client_name = models.CharField(max_length=200, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-updated_at"]
    def __str__(self): return self.title

class Document(models.Model):
    DOCUMENT_TYPES = [(x, x.replace("_", " ").title()) for x in ["revision_request", "report_excerpt", "report_pdf", "engagement_letter", "mls_csv", "appraiser_notes", "uad_issue", "public_record", "other"]]
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=40, choices=DOCUMENT_TYPES, default="other")
    file = models.FileField(upload_to="assignment_documents/", blank=True)
    pasted_text = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

