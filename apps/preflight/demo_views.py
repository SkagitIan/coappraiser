import json
import logging
import secrets
import time
import zipfile
from pathlib import Path

from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.views.decorators.http import require_GET, require_POST

from .demo_scenarios import DEMO_SCENARIOS, scenario_package_path, scenario_snapshot_path
from .demo_snapshots import load_demo_snapshot
from .demo_services import (
    cleanup_expired_demo_users,
    create_demo_review,
    demo_review_steps,
    get_session_demo_user,
    process_demo_review,
    reset_failed_demo_review,
)
from .models import FindingDecision, PreflightReview, ReviewFile, ReviewFinding
from .services import build_workfile_record
from .views import build_detail_context


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
    context = build_detail_context(review)
    snapshot = load_demo_snapshot(slug)
    context.update({
        "scenario": scenario,
        "scenario_slug": slug,
        "demo_mode": True,
        "demo_snapshot": snapshot,
    })
    return context


def _package_member_count(scenario):
    with zipfile.ZipFile(scenario_package_path(scenario)) as archive:
        return len([name for name in archive.namelist() if not name.endswith("/")])


@require_GET
def landing(request):
    cleanup_expired_demo_users()
    launch_token = secrets.token_urlsafe(24)
    request.session[DEMO_LAUNCH_TOKEN_KEY] = launch_token
    scenarios = []
    for slug, scenario in DEMO_SCENARIOS.items():
        item = dict(scenario)
        item["slug"] = slug
        item["available"] = scenario_package_path(scenario).is_file() and scenario_snapshot_path(slug).is_file()
        item["member_count"] = _package_member_count(scenario) if scenario_package_path(scenario).is_file() else 0
        item["start_url"] = reverse("preflight_demo:start", args=[slug])
        scenarios.append(item)
    return render(
        request,
        "preflight/demo/landing.html",
        {
            "scenarios": scenarios,
            "launch_token": launch_token,
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
    return render(request, "preflight/demo/progress.html", {
        "review": review,
        "scenario": scenario,
        "scenario_slug": slug,
        "package_member_count": _package_member_count(scenario),
    })


@require_POST
def process(request, pk):
    review = _demo_review_or_404(request, pk)
    slug, scenario = _scenario_for_review(review)
    try:
        state, review, _ = process_demo_review(review, scenario, slug)
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


@require_POST
def stream(request, pk):
    review = _demo_review_or_404(request, pk)
    slug, scenario = _scenario_for_review(review)

    def generate():
        try:
            for step in demo_review_steps(review, scenario, slug):
                if step["kind"] == "state":
                    if step["state"] == "completed":
                        yield json.dumps({
                            "kind": "complete",
                            "title": "Preflight ready",
                            "detail": "Opening the recorded review.",
                            "redirect": reverse("preflight_demo:detail", args=[review.pk]),
                        }) + "\n"
                    elif step["state"] == "busy":
                        yield json.dumps({
                            "kind": "active",
                            "title": "Review already in progress",
                            "detail": "Waiting for the existing demo run to finish.",
                        }) + "\n"
                    return
                payload = {key: value for key, value in step.items() if key not in {"review", "version", "execution", "state"}}
                if step["kind"] == "complete":
                    payload["redirect"] = reverse("preflight_demo:detail", args=[review.pk])
                yield json.dumps(payload) + "\n"
                if step["kind"] != "complete":
                    time.sleep(0.55)
        except Exception:
            logger.exception("Public demo stream failed for review %s", review.pk)
            yield json.dumps({
                "kind": "error",
                "title": "Demo review could not finish",
                "detail": "The selected package remains isolated to this session. Return to the demo and try again.",
            }) + "\n"

    response = StreamingHttpResponse(generate(), content_type="application/x-ndjson")
    response["Cache-Control"] = "no-cache, no-store"
    response["X-Accel-Buffering"] = "no"
    return response


@require_GET
def detail(request, pk):
    review = _demo_review_or_404(request, pk)
    slug, scenario = _scenario_for_review(review)
    return render(request, "preflight/detail.html", _findings_context(review, scenario, slug))


@require_POST
def retry(request, pk):
    review = _demo_review_or_404(request, pk)
    slug, scenario = _scenario_for_review(review)
    if review.status == "failed":
        reset_failed_demo_review(review)
        return render(request, "preflight/demo/progress.html", {
            "review": review,
            "scenario": scenario,
            "scenario_slug": slug,
            "package_member_count": _package_member_count(scenario),
        })

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
