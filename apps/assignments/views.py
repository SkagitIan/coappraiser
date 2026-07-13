from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import AssignmentForm, DocumentForm
from .models import Assignment
from apps.workfile.models import VerificationItem
from apps.ai_tools.services.file_tools import extract_pdf_text

@login_required
def dashboard(request):
    assignments = Assignment.objects.filter(user=request.user)
    open_items = VerificationItem.objects.filter(assignment__user=request.user, status="open")[:8]
    return render(request, "assignments/dashboard.html", {"assignments": assignments, "open_items": open_items})

@login_required
def assignment_create(request):
    form = AssignmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)
        assignment.user = request.user
        assignment.save()
        return redirect("assignments:detail", assignment.pk)
    return render(request, "assignments/form.html", {"form": form})

@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    doc_form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and doc_form.is_valid():
        doc = doc_form.save(commit=False)
        doc.assignment = assignment
        doc.original_filename = getattr(doc.file, "name", "")
        doc.save()
        if doc.file and doc.original_filename.lower().endswith(".pdf"):
            try:
                doc.file.open("rb")
                doc.extracted_text = extract_pdf_text(doc.file)
                doc.file.close()
                doc.save(update_fields=["extracted_text"])
            except ValueError:
                pass
        elif doc.file and doc.original_filename.lower().endswith((".txt", ".md")):
            doc.file.open("rb")
            doc.extracted_text = doc.file.read().decode("utf-8", errors="replace")
            doc.file.close()
            doc.save(update_fields=["extracted_text"])
        return redirect("assignments:detail", pk)
    skills = [
        {"slug": "revision-response", "name": "Revision Response Agent", "description": "Turn a reviewer or lender comment into a neutral response package.", "url": "ai_tools:revision_response"},
        {"slug": "uad-readiness", "name": "UAD 3.6 Readiness Review", "description": "Explain a potential issue without claiming official validation.", "url": "ai_tools:uad_issue_explainer"},
        {"slug": "market-evidence", "name": "Market Evidence Pack", "description": "Organize appraiser-provided MLS CSV evidence with cautious observations.", "url": "ai_tools:market_evidence"},
    ]
    return render(request, "assignments/detail.html", {"assignment": assignment, "document_form": doc_form, "skills": skills})
