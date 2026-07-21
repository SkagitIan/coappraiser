from django.conf import settings
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

def robots_txt(request):
    site_url = settings.COAPPRAISER_SITE_URL.rstrip("/")
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /app/",
            "Disallow: /billing/",
            "Disallow: /accounts/",
            "Disallow: /demo/reviews/",
            f"Sitemap: {site_url}/sitemap.xml",
            "",
        ]
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    site_url = settings.COAPPRAISER_SITE_URL.rstrip("/")
    pages = (
        ("/", "weekly", "1.0"),
        ("/demo/", "weekly", "0.9"),
        ("/faq/", "monthly", "0.8"),
        ("/pricing/", "monthly", "0.7"),
        ("/contact/", "yearly", "0.4"),
        ("/terms/", "yearly", "0.2"),
    )
    urls = "".join(
        f"<url><loc>{site_url}{path}</loc><changefreq>{frequency}</changefreq><priority>{priority}</priority></url>"
        for path, frequency, priority in pages
    )
    body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return HttpResponse(body, content_type="application/xml; charset=utf-8")
