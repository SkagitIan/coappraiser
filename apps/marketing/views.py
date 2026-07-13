from pathlib import Path
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render

def home(request):
    return render(request, "marketing/home.html")

PUBLIC_PAGE_MAP = {
    "early-access": "early-access/index.html",
    "pricing": "pricing/index.html",
    "skill-library": "skill-library/index.html",
    "uad-36-readiness-checklist": "uad-36-readiness-checklist/index.html",
    "solutions/uad-36-compliance-copilot": "solutions/uad-36-compliance-copilot/index.html",
    "solutions/revision-response-agent": "solutions/revision-response-agent/index.html",
    "solutions/market-evidence-pack": "solutions/market-evidence-pack/index.html",
    "solutions/workfile-guardian": "solutions/workfile-guardian/index.html",
}

def legacy_page(request, page):
    relative = PUBLIC_PAGE_MAP.get(page)
    if not relative:
        raise Http404
    path = Path(settings.BASE_DIR) / relative
    if not path.exists():
        raise Http404
    content = path.read_text(encoding="utf-8")
    if page != "early-access":
        content = content.replace('href="/early-access/"', 'href="/pricing/"')
        content = content.replace("Join early access", "View plans")
        content = content.replace("Request early access", "View plans")
    return HttpResponse(content, content_type="text/html")
