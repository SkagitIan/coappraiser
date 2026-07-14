from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import Lead


def home(request):
    return render(request, "marketing/home.html")


def health(request):
    return HttpResponse("ok", content_type="text/plain")


PUBLIC_PAGE_MAP = {
    "early-access": "early-access/index.html",
    "pricing": "pricing/index.html",
    "skill-library": "skill-library/index.html",
    "starter-pack": "starter-pack/index.html",
    "uad-36-readiness-checklist": "uad-36-readiness-checklist/index.html",
    "solutions/uad-36-compliance-copilot": "solutions/uad-36-compliance-copilot/index.html",
    "solutions/revision-response-agent": "solutions/revision-response-agent/index.html",
    "solutions/market-evidence-pack": "solutions/market-evidence-pack/index.html",
    "solutions/workfile-guardian": "solutions/workfile-guardian/index.html",
}


def legacy_page(request, page):
    if page in {"early-access", "starter-pack", "skill-library"} or page.startswith("solutions/"):
        return redirect("home")
    relative = PUBLIC_PAGE_MAP.get(page)
    if not relative:
        raise Http404
    path = Path(settings.BASE_DIR) / relative
    if not path.exists():
        raise Http404
    return HttpResponse(path.read_text(encoding="utf-8"), content_type="text/html")


def skill_page(request, path):
    return redirect("home")


def _client_is_bot(request):
    # Honeypot field: real visitors leave it empty.
    return bool(request.POST.get("website", "").strip())


def contact(request):
    sent = False
    if request.method == "POST" and not _client_is_bot(request):
        email = request.POST.get("email", "").strip()
        if email:
            Lead.objects.create(
                kind="contact",
                name=request.POST.get("name", "").strip()[:120],
                email=email[:254],
                message=request.POST.get("message", "").strip()[:5000],
                source_page=request.POST.get("source", "/contact/")[:200],
            )
            sent = True
    return render(request, "marketing/contact.html", {"sent": sent})


@csrf_exempt
def checklist_signup(request):
    # Lead-capture form on the statically served UAD 3.6 checklist page.
    if request.method != "POST":
        return redirect("uad_checklist")
    if not _client_is_bot(request):
        email = request.POST.get("email", "").strip()
        if email:
            Lead.objects.create(
                kind="checklist",
                name=request.POST.get("name", "").strip()[:120],
                email=email[:254],
                source_page="/uad-36-readiness-checklist/",
            )
    return render(request, "marketing/checklist_thanks.html")
