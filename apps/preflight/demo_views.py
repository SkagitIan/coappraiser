import json
import logging
import secrets
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.views.decorators.http import require_GET, require_POST

from .ai_review import run_preflight_ai_review
from .demo_scenarios import DEMO_SCENARIOS, scenario_package_path
from .demo_services import (
    cleanup_expired_demo_users,
    create_demo_review,
    get_session_demo_user,
    process_demo_review,
    reset_failed_demo_review,
)
from .models import FindingDecision, PreflightReview, ReviewFile, ReviewFinding
from .services import build_workfile_record


logger = logging.getLogger(__name__)
DEMO_LAUNCH_TOKEN_KEY = "coappraiser_demo_launch_token"


def _scenario_or_404(slug):
    scenario = DEMO_SCENARIOS.get(slug)
    if not scenario or not scenario_package_path(scenario).is_file():
        raise Http404
    return scenario


def _demo_review_or_404(request, pk):
    demo_user = get_session_demo_user(request)
    if not demo_user:
        raise Http404
    return get_object_or_404(PreflightReview, pk=pk, user=demo_user)


def _scenario_for_review(review):
    for slug, scenario in DEMO_SCENARIOS.items():
        if review.title == scenario["title"] and review.subject_identifier == scenario["subject_identifier"]:
            return slug, scenario
    raise Http404


def _findings_context(review, scenario, slug):
    version = review.versions.first()
    findings = list(version.findings.select_related("decision").all()) if version else []
    severity_rank = {"critical": 0, "warning": 1, "advisory": 2}
    findings.sort(key=lambda item: (severity_rank.get(item.severity, 3), 0 if item.basis == "deterministic" else 1, item.created_at))
    deterministic_findings = [item for item in findings if item.basis == "deterministic"]
    ai_findings = [item for item in findings if item.basis == "ai_interpretation"]
    ai_execution = version.ai_executions.order_by("-created_at").first() if version else None
    highest_severity = findings[0].get_severity_display() if findings else "None"
    return {
        "review": review,
        "version": version,
        "findings": findings,
        "deterministic_findings": deterministic_findings,
        "ai_findings": ai_findings,
        "observations": version.observations.all() if version else [],
        "ai_execution": ai_execution,
        "scenario": scenario,
        "scenario_slug": slug,
        "highest_severity": highest_severity,
        "demo_mode": True,
    }


@require_GET
def landing(request):
    cleanup_expired_demo_users()
    launch_token = secrets.token_urlsafe(24)
    request.session[DEMO_LAUNCH_TOKEN_KEY] = launch_token
    scenarios = []
    for slug, scenario in DEMO_SCENARIOS.items():
        item = dict(scenario)
        item["slug"] = slug
        item["available"] = scenario_package_path(scenario).is_file()
        scenarios.append(item)
    featured_scenario = next(item for item in scenarios if item["slug"] == "reconcile")
    alternate_scenarios = [item for item in scenarios if item["slug"] != "reconcile"]
    uses_live_gpt = (
        settings.COAPPRAISER_LLM_PROVIDER == "openai"
        and settings.COAPPRAISER_LLM_MODEL == "gpt-5.6"
    )
    return render(
        request,
        "preflight/demo/landing.html",
        {
            "scenarios": scenarios,
            "featured_scenario": featured_scenario,
            "alternate_scenarios": alternate_scenarios,
            "launch_token": launch_token,
            "uses_live_gpt": uses_live_gpt,
        },
    )


@require_POST
def start(request, slug):
    scenario = _scenario_or_404(slug)
    supplied_token = request.POST.get("launch_token", "")
    expected_token = request.session.pop(DEMO_LAUNCH_TOKEN_KEY, "")
    if not supplied_token or not expected_token or not constant_time_compare(supplied_token, expected_token):
        return HttpResponseBadRequest("This demo launch link was already used or expired. Return to the demo page and try again.")
    review = create_demo_review(request, scenario)
    request.session["coappraiser_demo_review_id"] = review.pk
    return render(request, "preflight/demo/progress.html", {"review": review, "scenario": scenario, "scenario_slug": slug})


@require_POST
def process(request, pk):
    review = _demo_review_or_404(request, pk)
    slug, scenario = _scenario_for_review(review)
    try:
        state, review, _ = process_demo_review(review, scenario)
    except Exception:
        logger.exception("Public demo processing failed for review %s", review.pk)
        state = "failed"
    if state == "busy":
        return render(request, "preflight/demo/partials/processing_wait.html", {"review": review}, status=202)
    destination = reverse("preflight_demo:detail", args=[review.pk])
    if request.headers.get("HX-Request") == "true":
        response = HttpResponse(status=204)
        response["HX-Redirect"] = destination
        return response
    return redirect(destination)


@require_GET
def detail(request, pk):
    review = _demo_review_or_404(request, pk)
    slug, scenario = _scenario_for_review(review)
    return render(request, "preflight/demo/detail.html", _findings_context(review, scenario, slug))


@require_POST
def retry(request, pk):
    review = _demo_review_or_404(request, pk)
    slug, scenario = _scenario_for_review(review)
    if review.status == "failed":
        reset_failed_demo_review(review)
        return render(request, "preflight/demo/progress.html", {"review": review, "scenario": scenario, "scenario_slug": slug})

    version = review.versions.first()
    ai_execution = version.ai_executions.order_by("-created_at").first() if version else None
    if version and ai_execution and ai_execution.status == "failed":
        version.findings.filter(basis="ai_interpretation").delete()
        version.ai_executions.all().delete()
        run_preflight_ai_review(version)

    return redirect("preflight_demo:detail", pk=review.pk)


@require_POST
def decision(request, pk):
    demo_user = get_session_demo_user(request)
    if not demo_user:
        raise Http404
    finding = get_object_or_404(ReviewFinding, pk=pk, review__user=demo_user)
    status = request.POST.get("status", "open")
    if status in dict(FindingDecision.STATUS_CHOICES):
        FindingDecision.objects.update_or_create(
            finding=finding,
            defaults={
                "status": status,
                "note": request.POST.get("note", "").strip()[:2000],
                "decided_by": demo_user,
            },
        )
    finding.refresh_from_db()
    return render(request, "preflight/partials/finding_status.html", {"finding": finding, "demo_mode": True})


@require_GET
def workfile(request, pk):
    review = _demo_review_or_404(request, pk)
    slug, scenario = _scenario_for_review(review)
    record = build_workfile_record(review)
    return render(
        request,
        "preflight/demo/workfile.html",
        {"review": review, "scenario": scenario, "scenario_slug": slug, "record": record, "snapshot": record.snapshot},
    )


@require_GET
def workfile_download(request, pk):
    review = _demo_review_or_404(request, pk)
    record = build_workfile_record(review)
    response = HttpResponse(json.dumps(record.snapshot, indent=2), content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="coappraiser-demo-workfile-{review.pk}.json"'
    return response


@require_GET
def download_file(request, pk):
    demo_user = get_session_demo_user(request)
    if not demo_user:
        raise Http404
    review_file = get_object_or_404(ReviewFile, pk=pk, version__review__user=demo_user)
    return FileResponse(review_file.file.open("rb"), as_attachment=True, filename=Path(review_file.original_name).name)
