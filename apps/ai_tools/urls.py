from django.urls import path
from . import views
app_name = "ai_tools"
urlpatterns = [
    path("<int:pk>/revision-response/", views.revision_response, name="revision_response"),
    path("<int:pk>/revision-response/generate/", views.generate_revision, name="generate_revision"),
    path("artifacts/<int:pk>/save/", views.save_artifact, name="save_artifact"),
    path("artifacts/<int:pk>/approve/", views.approve_artifact, name="approve_artifact"),
    path("<int:pk>/uad-readiness/", views.uad_issue_explainer, name="uad_issue_explainer"),
    path("<int:pk>/uad-readiness/generate/", views.generate_uad_issue, name="generate_uad_issue"),
    path("<int:pk>/market-evidence/", views.market_evidence, name="market_evidence"),
    path("<int:pk>/market-evidence/generate/", views.generate_market_evidence, name="generate_market_evidence"),
]
