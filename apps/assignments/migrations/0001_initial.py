from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [(migrations.swappable_dependency(settings.AUTH_USER_MODEL))]
    operations = [
        migrations.CreateModel(name="Assignment", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=200)), ("property_address", models.CharField(blank=True, max_length=300)),
            ("assignment_type", models.CharField(blank=True, max_length=100)), ("client_name", models.CharField(blank=True, max_length=200)),
            ("effective_date", models.DateField(blank=True, null=True)), ("status", models.CharField(choices=[("active", "Active"), ("complete", "Complete"), ("archived", "Archived")], default="active", max_length=20)),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-updated_at"]}),
        migrations.CreateModel(name="Document", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title", models.CharField(max_length=200)),
            ("document_type", models.CharField(choices=[(x, x.replace("_", " ").title()) for x in ["revision_request", "report_excerpt", "report_pdf", "engagement_letter", "mls_csv", "appraiser_notes", "uad_issue", "public_record", "other"]], default="other", max_length=40)),
            ("file", models.FileField(blank=True, upload_to="assignment_documents/")), ("pasted_text", models.TextField(blank=True)), ("extracted_text", models.TextField(blank=True)), ("original_filename", models.CharField(blank=True, max_length=255)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="assignments.assignment")),
        ]),
    ]

