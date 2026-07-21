from django.conf import settings


PUBLIC_PAGE_SEO = {
    "home": {
        "title": "CoAppraiser Preflight | Residential Appraisal Review",
        "description": "Catch contradictions across appraisal XML, rendered reports, commentary, and selected photos before client delivery.",
        "path": "/",
    },
    "pricing": {
        "title": "CoAppraiser Pricing | First Preflight Review Free",
        "description": "Run your first CoAppraiser Preflight review free, then continue with pre-delivery evidence review for residential appraisal packages.",
        "path": "/pricing/",
    },
    "faq": {
        "title": "Residential Appraiser FAQ | CoAppraiser Preflight",
        "description": "Answers about CoAppraiser Preflight, appraisal evidence review, data security, professional judgment, pricing, XML, PDFs, and photos.",
        "path": "/faq/",
    },
    "contact": {
        "title": "Contact CoAppraiser | Preflight Support",
        "description": "Contact CoAppraiser with questions about Preflight appraisal review, accounts, pricing, or the public demonstration.",
        "path": "/contact/",
    },
    "terms": {
        "title": "Terms and Conditions | CoAppraiser",
        "description": "Terms governing use of CoAppraiser Preflight and its AI-assisted residential appraisal evidence-review workflow.",
        "path": "/terms/",
    },
    "demo": {
        "title": "CoAppraiser Preflight Demo | Review a Sample Appraisal",
        "description": "Run a private-data-free demonstration of CoAppraiser Preflight across synthetic appraisal XML, PDF, commentary, and photo evidence.",
        "path": "/demo/",
    },
}


def seo(request):
    site_url = settings.COAPPRAISER_SITE_URL.rstrip("/")
    match = getattr(request, "resolver_match", None)
    url_name = getattr(match, "url_name", "") if match else ""
    namespace = getattr(match, "namespace", "") if match else ""

    page_key = url_name if url_name in PUBLIC_PAGE_SEO else ""
    if namespace == "preflight_demo" and url_name == "landing":
        page_key = "demo"

    page = PUBLIC_PAGE_SEO.get(page_key)
    if page:
        canonical_url = f"{site_url}{page['path']}"
        robots = "index,follow,max-image-preview:large"
        title = page["title"]
        description = page["description"]
    else:
        canonical_url = ""
        robots = "noindex,nofollow"
        title = "CoAppraiser Preflight"
        description = "Pre-delivery evidence review for residential appraisal packages."

    return {
        "seo": {
            "title": title,
            "description": description,
            "canonical_url": canonical_url,
            "robots": robots,
            "image_url": f"{site_url}{settings.STATIC_URL}social/coappraiser-preflight-share.png",
            "image_alt": "CoAppraiser Preflight reviewing a residential appraisal package before client delivery.",
            "site_url": site_url,
        }
    }