import json
import logging
from collections import Counter
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, When
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import PreflightReviewForm
from .models import FindingDecision, PreflightReview, ReviewFile, ReviewFinding
from .services import build_workfile_record, complete_review, delete_review_with_files, ingest_files, run_deterministic_review
from apps.billing.views import billing_mode, has_active_subscription

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    reviews = PreflightReview.objects.filter(user=request.user).prefetch_related("versions")
    return render(request, "preflight/dashboard.html", {"reviews": reviews, "review_count": reviews.count(), "completed_count": reviews.filter(status="completed").count(), "processing_count": reviews.filter(status="processing").count()})


@login_required
def create(request):
    if billing_mode() != "mock" and not has_active_subscription(request.user) and PreflightReview.objects.filter(user=request.user).exists():
        messages.info(request, "Your free Preflight scan has been used. Continue with the $59/month plan to review another package.")
        return redirect("billing:pricing")
    form = PreflightReviewForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        review = PreflightReview.objects.create(user=request.user, title=form.cleaned_data["title"], subject_identifier=form.cleaned_data["subject_identifier"], status="processing")
        version = review.versions.create(number=1, status="uploaded")
        try:
            uploaded = form.cleaned_data["files"]
            version.package_hash = "".join(sorted([str(getattr(f, "size", 0)) for f in uploaded]))[:64]
            version.save(update_fields=["package_hash"])
            ingest_files(version, uploaded)
        except Exception as exc:
            logger.exception("Preflight upload failed for review %s", review.pk)
            review.status = "failed"
            review.save(update_fields=["status", "updated_at"])
            form.add_error("files", "CoAppraiser could not process this package. The failed attempt was saved; try again with the exported ZIP or separate files.")
            return render(request, "preflight/form.html", {"form": form})
        return redirect("preflight:progress", review.pk)
    return render(request, "preflight/form.html", {"form": form})


def build_detail_context(review):
    version = review.versions.first()
    findings = version.findings.exclude(rule_code="PREFLIGHT_BASELINE").annotate(
        severity_rank=Case(
            When(severity="critical", then=0), When(severity="warning", then=1),
            default=2, output_field=IntegerField(),
        )
    ).order_by("severity_rank", "category", "created_at") if version else []
    deterministic_findings = findings.filter(basis="deterministic") if version else []
    ai_findings = findings.exclude(basis="deterministic") if version else []
    observations = version.observations.all() if version else []
    ai_execution = version.ai_executions.first() if version else None
    files = list(version.files.all()) if version else []
    kind_counts = Counter(item.kind for item in files)
    priority_counts = {
        "high": findings.filter(severity="critical").count() if version else 0,
        "medium": findings.filter(severity="warning").count() if version else 0,
        "low": findings.filter(severity="advisory").count() if version else 0,
    }
    inventory = [
        {
            "kind": kind,
            "label": {
                "pdf": "Rendered PDF",
                "xml": "XML",
                "image": "Photograph",
                "ssr": "SSR",
                "other": "Supporting file",
            }.get(kind, kind.title()),
            "count": kind_counts[kind],
        }
        for kind in ("pdf", "xml", "image", "ssr", "other")
        if kind_counts[kind]
    ]
    visual_manifest = []
    visual_coverage = []
    parsed_response = {}
    if ai_execution:
        visual_manifest = (
            (ai_execution.input_snapshot or {})
            .get("visual_review", {})
            .get("sources", [])
        )
        visual_coverage = (
            (ai_execution.input_snapshot or {})
            .get("visual_review", {})
            .get("coverage", [])
        )
        parsed_response = ai_execution.parsed_response or {}
    visual_photo_count = sum(item.get("kind") == "appraisal_photo" for item in visual_manifest)
    visual_pdf_count = sum(item.get("kind") == "rendered_pdf" for item in visual_manifest)
    pdf_page_count = sum(
        (item.extracted_text or "").count("[CoAppraiser PDF page")
        or bool((item.extracted_text or "").strip())
        for item in files
        if item.kind == "pdf"
    )
    suppressed_findings = parsed_response.get("suppressed_findings", [])
    missing_information = parsed_response.get("missing_information", [])
    ai_summary = parsed_response.get("summary", "")
    response_metadata = parsed_response.get("_response_metadata", {})
    duration_ms = response_metadata.get("duration_ms")
    if ai_execution and ai_execution.status == "completed":
        if ai_findings.exists():
            ai_outcome = f"The Preflight agent returned {ai_findings.count()} supported evidence relationship{'s' if ai_findings.count() != 1 else ''} for review."
        elif suppressed_findings:
            ai_outcome = f"The Preflight agent completed the review. {len(suppressed_findings)} candidate item{'s were' if len(suppressed_findings) != 1 else ' was'} withheld because the available evidence did not support an appraiser action."
        else:
            ai_outcome = "The Preflight agent completed the review and did not return an additional supported conflict."
    elif ai_execution and ai_execution.status == "failed":
        ai_outcome = "The Preflight agent could not complete this pass. Your uploaded package and repeatable checks remain saved."
    elif ai_execution and ai_execution.status == "skipped":
        ai_outcome = "The Preflight agent was not run because the package did not contain readable report evidence."
    else:
        ai_outcome = "The Preflight agent review has not completed."
    previous = review.versions.all()[1] if review.versions.count() > 1 else None
    current_signatures = {f.signature for f in findings}
    prior_signatures = {
        f.signature
        for f in previous.findings.exclude(rule_code="PREFLIGHT_BASELINE")
    } if previous else set()
    comparison = {"fixed": len(prior_signatures - current_signatures), "still_present": len(prior_signatures & current_signatures), "new": len(current_signatures - prior_signatures)} if previous else None
    return {
        "review": review,
        "version": version,
        "findings": findings,
        "deterministic_findings": deterministic_findings,
        "ai_findings": ai_findings,
        "observations": observations,
        "ai_execution": ai_execution,
        "comparison": comparison,
        "form": PreflightReviewForm(initial={"title": review.title, "subject_identifier": review.subject_identifier}),
        "package_files": files,
        "inventory": inventory,
        "priority_counts": priority_counts,
        "package_complete": bool(kind_counts["pdf"] and kind_counts["xml"]),
        "pdf_page_count": pdf_page_count,
        "visual_manifest": visual_manifest,
        "visual_coverage": visual_coverage,
        "visual_photo_count": visual_photo_count,
        "visual_pdf_count": visual_pdf_count,
        "package_image_count": kind_counts["image"],
        "all_photos_reviewed": bool(kind_counts["image"]) and visual_photo_count == kind_counts["image"],
        "visual_skipped": [item for item in visual_coverage if item.get("status") == "skipped"],
        "duration_ms": duration_ms,
        "suppressed_findings": suppressed_findings,
        "missing_information": missing_information,
        "ai_summary": ai_summary,
        "ai_outcome": ai_outcome,
    }


@login_required
def detail(request, pk):
    review = get_object_or_404(PreflightReview.objects.prefetch_related("versions", "findings__decision"), pk=pk, user=request.user)
    return render(request, "preflight/detail.html", build_detail_context(review))


@login_required
def progress(request, pk):
    review = get_object_or_404(PreflightReview, pk=pk, user=request.user)
    if review.status == "completed":
        return redirect("preflight:detail", pk)
    return render(request, "preflight/progress.html", {"review": review, "version": review.versions.first()})


@login_required
@require_POST
def stream_review(request, pk):
    review = get_object_or_404(PreflightReview, pk=pk, user=request.user)
    version = review.versions.first()

    def event(kind, title, detail="", **extra):
        return json.dumps({"kind": kind, "title": title, "detail": detail, **extra}) + "\n"

    def generate():
        try:
            review.refresh_from_db()
            version.refresh_from_db()
            if review.status == "completed":
                yield event("complete", "Preflight complete", redirect=reverse("preflight:detail", args=[review.pk]))
                return

            file_count = version.files.count()
            yield event("complete_step", "Package stored", f"{file_count} file{'s' if file_count != 1 else ''} secured for this review.")

            if not version.findings.exists():
                yield event("active", "Normalizing package evidence", "Tracing supported UAD fields, rendered report text, and package contents back to their sources.")
                deterministic = run_deterministic_review(version, include_ai=False)
            else:
                deterministic = list(version.findings.filter(basis="deterministic"))

            observation_count = version.observations.count()
            yield event("complete_step", "Evidence normalized", f"{observation_count} traceable observation{'s' if observation_count != 1 else ''} retained with source locations.")
            yield event("complete_step", "Cross-source checks complete", f"{len(deterministic)} repeatable rule-based item{'s' if len(deterministic) != 1 else ''} recorded.")
            for finding in deterministic:
                yield event("finding", "Preflight check recorded", finding.title)

            execution = version.ai_executions.first()
            if execution is None:
                from .ai_review import run_preflight_ai_review
                yield event("active", "Preflight agent evidence review", "Cross-checking the rendered report, selected photos, and normalized evidence.")
                execution = run_preflight_ai_review(version)

            ai_findings = list(version.findings.exclude(basis="deterministic"))
            if execution.status == "failed":
                yield event("warning", "Agent review unavailable", "Your uploaded package, normalized evidence, and rule-based findings are preserved.")
            else:
                visual_coverage = (
                    (execution.input_snapshot or {})
                    .get("visual_review", {})
                    .get("coverage", [])
                )
                reviewed_photos = sum(
                    item.get("kind") == "appraisal_photo" and item.get("status") == "reviewed"
                    for item in visual_coverage
                )
                package_photos = sum(item.kind == "image" for item in version.files.all())
                coverage_detail = (
                    f" {reviewed_photos} of {package_photos} package photo"
                    f"{'s' if package_photos != 1 else ''} supplied for visual review."
                    if visual_coverage
                    else ""
                )
                yield event(
                    "complete_step",
                    "Evidence review complete",
                    f"{len(ai_findings)} evidence-backed Preflight item{'s' if len(ai_findings) != 1 else ''} accepted."
                    + coverage_detail,
                )
                for finding in ai_findings:
                    yield event("finding", "Preflight evidence finding", finding.title)

            complete_review(version)
            yield event("complete", "Preflight ready", "Opening the action queue.", redirect=reverse("preflight:detail", args=[review.pk]))
        except Exception:
            logger.exception("Preflight streaming review failed for review %s", review.pk)
            version.status = "failed"
            version.save(update_fields=["status"])
            review.status = "failed"
            review.save(update_fields=["status", "updated_at"])
            yield event("error", "Review could not finish", "The uploaded package remains saved. Retry the review or upload a revised package.")

    response = StreamingHttpResponse(generate(), content_type="application/x-ndjson")
    response["Cache-Control"] = "no-cache, no-store"
    response["X-Accel-Buffering"] = "no"
    return response


@login_required
@require_POST
def decision(request, pk):
    finding = get_object_or_404(ReviewFinding, pk=pk, review__user=request.user)
    status = request.POST.get("status", "open")
    if status in dict(FindingDecision.STATUS_CHOICES):
        FindingDecision.objects.update_or_create(finding=finding, defaults={"status": status, "note": request.POST.get("note", "").strip()[:2000], "decided_by": request.user})
    return render(request, "preflight/partials/finding_status.html", {"finding": finding})


@login_required
@require_POST
def revise(request, pk):
    review = get_object_or_404(PreflightReview, pk=pk, user=request.user)
    files = request.FILES.getlist("files")
    if not files:
        return redirect("preflight:detail", pk)
    version = review.versions.create(number=review.versions.count() + 1, status="uploaded")
    try:
        ingest_files(version, files)
    except Exception:
        logger.exception("Preflight revised upload failed for review %s", review.pk)
        review.status = "failed"
        review.save(update_fields=["status", "updated_at"])
    return redirect("preflight:progress", pk)


@login_required
@require_POST
def workfile_record(request, pk):
    review = get_object_or_404(PreflightReview, pk=pk, user=request.user)
    record = build_workfile_record(review)
    response = HttpResponse(json.dumps(record.snapshot, indent=2), content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="preflight-review-{review.pk}.json"'
    return response


@login_required
@require_POST
def delete_review(request, pk):
    review = get_object_or_404(PreflightReview, pk=pk, user=request.user)
    delete_review_with_files(review)
    messages.success(request, "The Preflight review and its uploaded files were deleted.")
    return redirect("preflight:dashboard")


@login_required
def download_file(request, pk):
    review_file = get_object_or_404(ReviewFile, pk=pk, version__review__user=request.user)
    return FileResponse(review_file.file.open("rb"), as_attachment=True, filename=review_file.original_name)
