import hashlib
import time
from datetime import datetime, timedelta
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.utils import timezone

from .demo_scenarios import scenario_package_path
from .models import PreflightReview
from .services import delete_review_with_files, ingest_files, run_deterministic_review


DEMO_USERNAME_PREFIX = "__coappraiser_demo__"
DEMO_SESSION_USER_KEY = "coappraiser_demo_user_id"
DEMO_SESSION_STARTED_KEY = "coappraiser_demo_started_at"
DEMO_PROCESSING_PREFIX = "demo-processing:"


def demo_retention():
    return timedelta(hours=settings.COAPPRAISER_DEMO_RETENTION_HOURS)


def cleanup_expired_demo_users(limit=10):
    User = get_user_model()
    cutoff = timezone.now() - demo_retention()
    users = list(
        User.objects.filter(username__startswith=DEMO_USERNAME_PREFIX, date_joined__lt=cutoff)
        .order_by("date_joined")[:limit]
    )
    for user in users:
        for review in list(user.preflight_reviews.all()):
            delete_review_with_files(review)
        user.delete()
    return len(users)


def get_or_create_demo_user(request):
    User = get_user_model()
    user_id = request.session.get(DEMO_SESSION_USER_KEY)
    started_raw = request.session.get(DEMO_SESSION_STARTED_KEY)
    started_at = None
    if started_raw:
        try:
            started_at = datetime.fromisoformat(started_raw)
            if timezone.is_naive(started_at):
                started_at = timezone.make_aware(started_at)
        except (TypeError, ValueError):
            started_at = None
    if started_at and started_at >= timezone.now() - demo_retention():
        user = User.objects.filter(pk=user_id, username__startswith=DEMO_USERNAME_PREFIX).first()
        if user:
            return user
    user = User(username=f"{DEMO_USERNAME_PREFIX}{uuid4().hex}")
    user.set_unusable_password()
    user.save()
    request.session[DEMO_SESSION_USER_KEY] = user.pk
    request.session[DEMO_SESSION_STARTED_KEY] = timezone.now().isoformat()
    return user


def get_session_demo_user(request):
    user_id = request.session.get(DEMO_SESSION_USER_KEY)
    if not user_id:
        return None
    return get_user_model().objects.filter(pk=user_id, username__startswith=DEMO_USERNAME_PREFIX).first()


def create_demo_review(request, scenario):
    user = get_or_create_demo_user(request)
    review = PreflightReview.objects.create(
        user=user,
        title=scenario["title"],
        subject_identifier=scenario["subject_identifier"],
        status="processing",
    )
    review.versions.create(number=1, status="uploaded")
    return review


def _claim_demo_processing(review):
    with transaction.atomic():
        locked = PreflightReview.objects.select_for_update().get(pk=review.pk)
        version = locked.versions.select_for_update().get(number=1)
        if locked.status in {"completed", "failed"}:
            return locked.status, locked, version
        if version.package_hash.startswith(DEMO_PROCESSING_PREFIX):
            try:
                started = float(version.package_hash.removeprefix(DEMO_PROCESSING_PREFIX))
            except ValueError:
                started = time.time()
            if time.time() - started > settings.COAPPRAISER_DEMO_STALE_PROCESSING_SECONDS:
                locked.status = "failed"
                locked.save(update_fields=["status", "updated_at"])
                version.status = "failed"
                version.save(update_fields=["status"])
                return "failed", locked, version
            return "busy", locked, version
        version.package_hash = f"{DEMO_PROCESSING_PREFIX}{int(time.time())}"
        version.save(update_fields=["package_hash"])
        return "claimed", locked, version


def process_demo_review(review, scenario):
    state, review, version = _claim_demo_processing(review)
    if state != "claimed":
        return state, review, version
    package_path = scenario_package_path(scenario)
    try:
        package_bytes = package_path.read_bytes()
        package_hash = hashlib.sha256(package_bytes).hexdigest()
        upload = SimpleUploadedFile(
            scenario["filename"],
            package_bytes,
            content_type="application/zip",
        )
        ingest_files(version, [upload])
        run_deterministic_review(version)
        version.package_hash = package_hash
        version.save(update_fields=["package_hash"])
        return "completed", review, version
    except Exception:
        review.status = "failed"
        review.save(update_fields=["status", "updated_at"])
        version.status = "failed"
        version.save(update_fields=["status"])
        raise


def reset_failed_demo_review(review):
    version = review.versions.get(number=1)
    for review_file in list(version.files.all()):
        if review_file.file:
            review_file.file.delete(save=False)
    version.files.all().delete()
    version.observations.all().delete()
    version.findings.all().delete()
    version.ai_executions.all().delete()
    version.package_hash = ""
    version.status = "uploaded"
    version.save(update_fields=["package_hash", "status"])
    review.status = "processing"
    review.save(update_fields=["status", "updated_at"])
