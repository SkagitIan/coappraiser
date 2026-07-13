from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from apps.ai_tools.models import AIActionLog
from apps.assignments.models import Assignment, Document
from apps.billing.models import Subscription
from apps.workfile.models import OutputArtifact, VerificationItem
from django.contrib.auth import get_user_model


@staff_member_required
def dashboard(request):
    return render(request, "admin/dashboard.html", {
        "user_count": get_user_model().objects.count(),
        "assignment_count": Assignment.objects.count(),
        "document_count": Document.objects.count(),
        "action_count": AIActionLog.objects.count(),
        "artifact_count": OutputArtifact.objects.count(),
        "open_verification_count": VerificationItem.objects.filter(status="open").count(),
        "active_subscription_count": Subscription.objects.filter(status__in=["active", "trialing"]).count(),
        "recent_actions": AIActionLog.objects.select_related("assignment", "created_by").order_by("-created_at")[:10],
    })
