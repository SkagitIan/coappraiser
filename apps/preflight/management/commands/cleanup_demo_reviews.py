from django.core.management.base import BaseCommand

from apps.preflight.demo_services import cleanup_expired_demo_users


class Command(BaseCommand):
    help = "Delete expired anonymous demo users, reviews, database records, and stored files."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **options):
        deleted = cleanup_expired_demo_users(limit=max(1, options["limit"]))
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired demo user(s)."))
