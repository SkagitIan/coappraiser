from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("preflight", "0004_finding_decision_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="reviewfinding",
            name="confidence",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.AddField(
            model_name="reviewfinding",
            name="visual_sources",
            field=models.JSONField(default=list),
        ),
    ]
