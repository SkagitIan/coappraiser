from django.conf import settings
from django.db import models
from apps.assignments.models import Assignment

class AIActionLog(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="ai_actions")
    skill_slug = models.CharField(max_length=100)
    action_type = models.CharField(max_length=100)
    input_snapshot = models.JSONField(default=dict)
    selected_document_references = models.JSONField(default=list)
    system_prompt_snapshot = models.TextField()
    model_provider = models.CharField(max_length=50, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    raw_response = models.TextField()
    parsed_response = models.JSONField(default=dict)
    status = models.CharField(max_length=30, default="completed")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

