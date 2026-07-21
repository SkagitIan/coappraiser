from django.contrib import admin
from django.urls import include, path
from apps.marketing.views import contact, faq, health, home, robots_txt, sitemap_xml, terms
from apps.billing.views import pricing as billing_pricing
from apps.marketing.admin_views import dashboard as admin_dashboard

urlpatterns = [
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"), path("admin/", admin.site.urls), path("health/", health, name="health"), path("robots.txt", robots_txt, name="robots"), path("sitemap.xml", sitemap_xml, name="sitemap"), path("", home, name="home"),
    path("demo/", include(("apps.preflight.demo_urls", "preflight_demo"), namespace="preflight_demo")),
    path("contact/", contact, name="contact"),
    path("faq/", faq, name="faq"),
    path("terms/", terms, name="terms"),
    path("pricing/", billing_pricing, name="pricing"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", include("apps.accounts.urls")),
    path("app/preflight/", include("apps.preflight.urls")),
    path("billing/", include("apps.billing.urls")),
]
