from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [("assignments", "0001_initial"), (migrations.swappable_dependency(settings.AUTH_USER_MODEL))]
    operations = [migrations.CreateModel(name="AIActionLog", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("skill_slug", models.CharField(max_length=100)), ("action_type", models.CharField(max_length=100)), ("input_snapshot", models.JSONField(default=dict)), ("selected_document_references", models.JSONField(default=list)), ("system_prompt_snapshot", models.TextField()), ("model_provider", models.CharField(blank=True, max_length=50)), ("model_name", models.CharField(blank=True, max_length=100)), ("raw_response", models.TextField()), ("parsed_response", models.JSONField(default=dict)), ("status", models.CharField(default="completed", max_length=30)), ("created_at", models.DateTimeField(auto_now_add=True)),
        ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_actions", to="assignments.assignment")), ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL))
    ])]

