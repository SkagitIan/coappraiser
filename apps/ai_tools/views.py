import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from apps.assignments.models import Assignment
from apps.workfile.models import OutputArtifact, VerificationItem
from .forms import RevisionResponseForm
from .forms import MarketEvidenceForm, UADIssueForm
from .models import AIActionLog
from .services.file_tools import analyze_csv
from .services.uad_issue import mock_uad_response
from .services.skill_loader import load_skill
from .services.llm_client import run_skill
from apps.billing.views import subscription_required

@login_required
@subscription_required
def revision_response(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    return render(request, "ai_tools/revision_response.html", {"assignment": assignment, "form": RevisionResponseForm()})

@login_required
@subscription_required
@require_POST
def generate_revision(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    form = RevisionResponseForm(request.POST)
    if not form.is_valid():
        return render(request, "ai_tools/partials/revision_form_errors.html", {"form": form})
    skill = load_skill("revision-response")
    data = form.cleaned_data
    prompt = f"REVISION REQUEST:\n{data['revision_request']}\nREPORT EXCERPT:\n{data['report_excerpt']}\nAPPRAISER NOTES:\n{data['appraiser_notes']}"
    result = run_skill(system_prompt=skill["instructions"], user_prompt=prompt, output_schema={})
    action = AIActionLog.objects.create(assignment=assignment, skill_slug=skill["slug"], action_type="revision_response", input_snapshot=data, system_prompt_snapshot=skill["instructions"], model_provider=settings.COAPPRAISER_LLM_PROVIDER, model_name=settings.COAPPRAISER_LLM_MODEL, raw_response=json.dumps(result), parsed_response=result, created_by=request.user)
    artifact = OutputArtifact.objects.create(assignment=assignment, title="Revision response draft", artifact_type="revision_response", source_action=action, original_generated_content=result, user_edited_content=result)
    for item in result.get("verification_items", []):
        VerificationItem.objects.create(assignment=assignment, artifact=artifact, description=item)
    return render(request, "ai_tools/partials/revision_output.html", {"assignment": assignment, "artifact": artifact, "result": result})

@login_required
@require_POST
def save_artifact(request, pk):
    artifact = get_object_or_404(OutputArtifact, pk=pk, assignment__user=request.user)
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            try:
                artifact.user_edited_content = json.loads(content)
            except json.JSONDecodeError:
                return render(request, "ai_tools/partials/save_status.html", {"artifact": artifact, "error": "The edited content could not be saved."})
        elif "draft_response" in request.POST:
            artifact.user_edited_content = {**artifact.user_edited_content, "draft_response": request.POST["draft_response"]}
        artifact.save()
    return render(request, "ai_tools/partials/save_status.html", {"artifact": artifact})

@login_required
@require_POST
def approve_artifact(request, pk):
    artifact = get_object_or_404(OutputArtifact, pk=pk, assignment__user=request.user)
    artifact.approval_status = "approved"
    artifact.approved_at = timezone.now()
    artifact.save()
    return render(request, "ai_tools/partials/save_status.html", {"artifact": artifact})

@login_required
@subscription_required
def uad_issue_explainer(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    return render(request, "ai_tools/uad_issue_explainer.html", {"assignment": assignment, "form": UADIssueForm()})

@login_required
@subscription_required
@require_POST
def generate_uad_issue(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    form = UADIssueForm(request.POST)
    if not form.is_valid():
        return render(request, "ai_tools/partials/revision_form_errors.html", {"form": form})
    issue = form.cleaned_data["issue_text"]
    skill = load_skill("uad-issue-explainer")
    result = mock_uad_response(issue)
    action = AIActionLog.objects.create(assignment=assignment, skill_slug=skill["slug"], action_type="uad_issue_explainer", input_snapshot=form.cleaned_data, system_prompt_snapshot=skill["instructions"], model_provider="mock", model_name="development-mock", raw_response=json.dumps(result), parsed_response=result, created_by=request.user)
    artifact = OutputArtifact.objects.create(assignment=assignment, title="UAD issue explanation", artifact_type="uad_issue_summary", source_action=action, original_generated_content=result, user_edited_content=result)
    for item in result["verification_items"]:
        VerificationItem.objects.create(assignment=assignment, artifact=artifact, description=item)
    return render(request, "ai_tools/partials/uad_output.html", {"result": result, "artifact": artifact})

@login_required
@subscription_required
def market_evidence(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    return render(request, "ai_tools/market_evidence.html", {"assignment": assignment, "form": MarketEvidenceForm()})

@login_required
@subscription_required
@require_POST
def generate_market_evidence(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    form = MarketEvidenceForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "ai_tools/partials/revision_form_errors.html", {"form": form})
    try:
        summary = analyze_csv(form.cleaned_data["csv_file"])
    except ValueError as exc:
        form.add_error("csv_file", str(exc))
        return render(request, "ai_tools/partials/revision_form_errors.html", {"form": form})
    skill = load_skill("market-evidence")
    result = {"market_summary": f"The file contains {summary['row_count']} rows. Sale-price records available for analysis: {summary['sale_price']['count']}.", "statistics": summary, "trend_observations": ["These descriptive statistics organize the provided sales data; they do not by themselves establish a market adjustment."], "caution_flags": ["Verify applicability to the subject market segment, property type, effective date, and selected comparable sales."], "report_language": "The provided sales data was reviewed for descriptive market evidence. The appraiser should verify applicability and determine whether any market conditions analysis is appropriate.", "workfile_note": "Market Evidence Pack summary generated from appraiser-provided CSV data. Retain the original export and verify the column mapping.", "verification_items": ["Confirm detected column mapping and review missing values.", "Confirm that any observed trend is applicable to the assignment."], "risk_flags": ["CoAppraiser does not determine a final adjustment."]}
    action = AIActionLog.objects.create(assignment=assignment, skill_slug=skill["slug"], action_type="market_evidence_pack", input_snapshot={"notes": form.cleaned_data["appraiser_notes"], "summary": summary}, system_prompt_snapshot=skill["instructions"], model_provider="deterministic", model_name="csv-analyzer", raw_response=json.dumps(result), parsed_response=result, created_by=request.user)
    artifact = OutputArtifact.objects.create(assignment=assignment, title="Market evidence memo", artifact_type="market_evidence_memo", source_action=action, original_generated_content=result, user_edited_content=result)
    for item in result["verification_items"]:
        VerificationItem.objects.create(assignment=assignment, artifact=artifact, description=item)
    return render(request, "ai_tools/partials/market_output.html", {"result": result, "artifact": artifact})
