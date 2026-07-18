from django.http import HttpResponse
from django.shortcuts import render

from .models import Lead


def home(request):
    return render(request, "marketing/home.html")


def health(request):
    return HttpResponse("ok", content_type="text/plain")


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


def terms(request):
    return render(request, "marketing/terms.html", {"public_page": True})


def faq(request):
    return render(request, "marketing/faq.html", {"public_page": True})
