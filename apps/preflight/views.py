import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import PreflightReviewForm
from .models import FindingDecision, PreflightReview, ReviewFile, ReviewFinding
from .services import build_workfile_record, delete_review_with_files, ingest_files, run_deterministic_review
from apps.billing.views import billing_mode, has_active_subscription


@login_required
def dashboard(request):
    reviews = PreflightReview.objects.filter(user=request.user).prefetch_related("versions")
    return render(request, "preflight/dashboard.html", {"reviews": reviews})


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
            run_deterministic_review(version)
        except (ValueError, OSError) as exc:
            review.status = "failed"
            review.save(update_fields=["status", "updated_at"])
            form.add_error("files", str(exc))
            return render(request, "preflight/form.html", {"form": form})
        return redirect("preflight:detail", review.pk)
    return render(request, "preflight/form.html", {"form": form})


@login_required
def detail(request, pk):
    review = get_object_or_404(PreflightReview.objects.prefetch_related("versions", "findings__decision"), pk=pk, user=request.user)
    version = review.versions.first()
    findings = version.findings.all() if version else []
    previous = review.versions.all()[1] if review.versions.count() > 1 else None
    current_signatures = {f.signature for f in findings}
    prior_signatures = {f.signature for f in previous.findings.all()} if previous else set()
    comparison = {"fixed": len(prior_signatures - current_signatures), "still_present": len(prior_signatures & current_signatures), "new": len(current_signatures - prior_signatures)} if previous else None
    return render(request, "preflight/detail.html", {"review": review, "version": version, "findings": findings, "comparison": comparison, "form": PreflightReviewForm(initial={"title": review.title, "subject_identifier": review.subject_identifier})})


@login_required
@require_POST
def decision(request, pk):
    finding = get_object_or_404(ReviewFinding, pk=pk, review__user=request.user)
    status = request.POST.get("status", "open")
    if status in dict(FindingDecision.STATUS_CHOICES):
        FindingDecision.objects.update_or_create(finding=finding, defaults={"status": status, "note": request.POST.get("note", ""), "decided_by": request.user})
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
        run_deterministic_review(version)
    except ValueError:
        review.status = "failed"
        review.save(update_fields=["status", "updated_at"])
    return redirect("preflight:detail", pk)


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
