import os
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.ai_tools.models import AIActionLog
from apps.assignments.models import Assignment, Document
from apps.billing.models import Subscription
from apps.workfile.models import OutputArtifact, VerificationItem


DEMO_USERNAME = "demo@coappraiser.com"


class Command(BaseCommand):
    help = "Create or refresh a non-staff CoAppraiser demo account and synthetic assignments."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=DEMO_USERNAME)
        parser.add_argument("--password", default=os.getenv("COAPPRAISER_DEMO_PASSWORD"))
        parser.add_argument("--reset", action="store_true", help="Delete existing demo assignments before reseeding.")

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        if not password:
            raise CommandError("Set COAPPRAISER_DEMO_PASSWORD or pass --password. Never commit demo credentials.")
        username = options["username"]
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={"email": username})
        user.email = username
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()

        if options["reset"]:
            Assignment.objects.filter(user=user).delete()

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "plan": "pro",
                "status": "active",
                "stripe_customer_id": "demo_customer_coappraiser",
                "stripe_subscription_id": None,
            },
        )

        assignments = [
            {
                "key": "revision",
                "title": "Demo · GLA revision response",
                "address": "1840 Cedar Ridge Lane, Example, WA",
                "type": "Residential appraisal",
                "docs": [("Reviewer request", "revision_request", "Please provide additional support for the GLA adjustment.")],
            },
            {
                "key": "market",
                "title": "Demo · Market evidence review",
                "address": "742 Maple View Drive, Example, WA",
                "type": "Market conditions analysis",
                "docs": [("Synthetic MLS export", "mls_csv", "sale_date,sale_price,list_price,dom\n2025-01-01,300000,305000,10\n2025-02-01,320000,325000,8\n2025-03-01,315000,318000,12\n")],
            },
            {
                "key": "uad",
                "title": "Demo · UAD 3.6 issue review",
                "address": "61 Orchard Loop, Example, WA",
                "type": "UAD readiness review",
                "docs": [("Potential issue text", "uad_issue", "Potential inconsistency in the reported finished area field.")],
            },
            {
                "key": "workfile",
                "title": "Demo · Workfile Guardian",
                "address": "920 Harbor Street, Example, WA",
                "type": "Residential appraisal",
                "docs": [("Assignment notes", "appraiser_notes", "Synthetic notes for demonstrating source history and verification tracking.")],
            },
        ]

        for item in assignments:
            assignment, _ = Assignment.objects.get_or_create(
                user=user,
                title=item["title"],
                defaults={"property_address": item["address"], "assignment_type": item["type"], "effective_date": date(2025, 3, 15)},
            )
            for title, document_type, pasted_text in item["docs"]:
                Document.objects.get_or_create(assignment=assignment, title=title, defaults={"document_type": document_type, "pasted_text": pasted_text, "original_filename": "synthetic-source.txt"})

        self.stdout.write(self.style.SUCCESS(f"Demo account ready: {username} ({'created' if created else 'refreshed'})"))
        self.stdout.write("Synthetic assignments: revision, market, uad, workfile")
