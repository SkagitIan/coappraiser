from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from django.conf import settings
from apps.marketing.views import health, home, legacy_page
from apps.billing.views import pricing as billing_pricing
from apps.marketing.admin_views import dashboard as admin_dashboard

urlpatterns = [
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"), path("admin/", admin.site.urls), path("health/", health, name="health"), path("", home, name="home"),
    path("assets/<path:path>", serve, {"document_root": settings.BASE_DIR / "assets"}),
    path("early-access/", legacy_page, {"page": "early-access"}, name="early_access"),
    path("pricing/", billing_pricing, name="pricing"),
    path("skill-library/", legacy_page, {"page": "skill-library"}, name="skill_library"),
    path("uad-36-readiness-checklist/", legacy_page, {"page": "uad-36-readiness-checklist"}, name="uad_checklist"),
    path("solutions/uad-36-compliance-copilot/", legacy_page, {"page": "solutions/uad-36-compliance-copilot"}, name="uad_solution_legacy"),
    path("solutions/revision-response-agent/", legacy_page, {"page": "solutions/revision-response-agent"}, name="revision_agent_legacy"),
    path("solutions/market-evidence-pack/", legacy_page, {"page": "solutions/market-evidence-pack"}, name="market_evidence_legacy"),
    path("solutions/workfile-guardian/", legacy_page, {"page": "solutions/workfile-guardian"}, name="workfile_legacy"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", include("apps.accounts.urls")),
    path("app/", include("apps.assignments.urls")),
    path("app/assignments/", include("apps.ai_tools.urls")),
    path("app/workfile/", include("apps.workfile.urls")),
    path("billing/", include("apps.billing.urls")),
]
