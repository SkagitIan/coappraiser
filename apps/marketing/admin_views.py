from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from apps.billing.models import Subscription
from apps.preflight.models import AIExecution, FindingDecision, PreflightReview, ReviewFile
from django.contrib.auth import get_user_model


@staff_member_required
def dashboard(request):
    return render(request, "admin/dashboard.html", {
        "user_count": get_user_model().objects.count(),
        "review_count": PreflightReview.objects.count(),
        "file_count": ReviewFile.objects.count(),
        "execution_count": AIExecution.objects.count(),
        "open_finding_count": FindingDecision.objects.filter(status="open").count(),
        "active_subscription_count": Subscription.objects.filter(status__in=["active", "trialing"]).count(),
        "recent_reviews": PreflightReview.objects.select_related("user").order_by("-updated_at")[:10],
    })
