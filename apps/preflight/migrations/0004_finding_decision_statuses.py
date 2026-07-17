from django.db import migrations, models


def update_legacy_statuses(apps, schema_editor):
    FindingDecision = apps.get_model("preflight", "FindingDecision")
    FindingDecision.objects.filter(status="dismissed").update(status="not_applicable")
    FindingDecision.objects.filter(status="accepted_risk").update(status="deferred")


def restore_legacy_statuses(apps, schema_editor):
    FindingDecision = apps.get_model("preflight", "FindingDecision")
    FindingDecision.objects.filter(status="not_applicable").update(status="dismissed")
    FindingDecision.objects.filter(status="deferred").update(status="accepted_risk")


class Migration(migrations.Migration):
    dependencies = [
        ("preflight", "0003_aiexecution"),
    ]

    operations = [
        migrations.RunPython(update_legacy_statuses, restore_legacy_statuses),
        migrations.AlterField(
            model_name="findingdecision",
            name="status",
            field=models.CharField(
                choices=[("open", "Open"), ("resolved", "Resolved"), ("deferred", "Deferred"), ("not_applicable", "Not Applicable")],
                default="open",
                max_length=20,
            ),
        ),
    ]
