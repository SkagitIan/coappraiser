from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [("assignments", "0001_initial"), ("ai_tools", "0001_initial")]
    operations = [
        migrations.CreateModel(name="OutputArtifact", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title", models.CharField(max_length=200)), ("artifact_type", models.CharField(choices=[(x, x.replace("_", " ").title()) for x in ["revision_response", "report_language", "workfile_note", "support_checklist", "uad_issue_summary", "market_evidence_memo", "qa_punch_list"]], max_length=50)), ("original_generated_content", models.JSONField(default=dict)), ("user_edited_content", models.JSONField(default=dict)), ("approval_status", models.CharField(choices=[("draft", "Draft"), ("approved", "Approved")], default="draft", max_length=20)), ("approved_at", models.DateTimeField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="artifacts", to="assignments.assignment")), ("source_action", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="artifacts", to="ai_tools.aiactionlog"))
        ]),
        migrations.CreateModel(name="VerificationItem", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("description", models.TextField()), ("status", models.CharField(choices=[("open", "Open"), ("verified", "Verified"), ("needs_more_info", "Needs more information"), ("not_applicable", "Not applicable")], default="open", max_length=30)), ("user_note", models.TextField(blank=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("completed_at", models.DateTimeField(blank=True, null=True)), ("artifact", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="verification_items", to="workfile.outputartifact")), ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_items", to="assignments.assignment"))
        ])
    ]

