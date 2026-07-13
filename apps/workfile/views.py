from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.assignments.models import Assignment
from .models import VerificationItem

@login_required
def detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    return render(request, "workfile/detail.html", {"assignment": assignment, "actions": assignment.ai_actions.all(), "artifacts": assignment.artifacts.all(), "items": assignment.verification_items.all()})

@login_required
@require_POST
def update_verification(request, pk):
    item = get_object_or_404(VerificationItem, pk=pk, assignment__user=request.user)
    if request.method == "POST":
        status = request.POST.get("status", "open")
        if status in dict(VerificationItem.STATUS_CHOICES):
            item.status = status
            item.user_note = request.POST.get("user_note", item.user_note)
            item.completed_at = None if status == "open" else timezone.now()
            item.save()
    return render(request, "workfile/partials/verification_status.html", {"item": item})
