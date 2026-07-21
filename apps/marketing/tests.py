from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(COAPPRAISER_SITE_URL="https://coappraiser.com")
class PublicSeoTests(TestCase):
    def test_public_pages_have_unique_search_and_social_metadata(self):
        pages = {
            "home": ("https://coappraiser.com/", "Residential Appraisal Review"),
            "pricing": ("https://coappraiser.com/pricing/", "First Preflight Review Free"),
            "faq": ("https://coappraiser.com/faq/", "Residential Appraiser FAQ"),
            "contact": ("https://coappraiser.com/contact/", "Contact CoAppraiser"),
            "terms": ("https://coappraiser.com/terms/", "Terms and Conditions"),
            "preflight_demo:landing": ("https://coappraiser.com/demo/", "Preflight Demo"),
        }
        for route_name, (canonical, expected_title) in pages.items():
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_title)
                self.assertContains(response, f'<link rel="canonical" href="{canonical}">', html=True)
                self.assertContains(response, 'name="robots" content="index,follow,max-image-preview:large"')
                self.assertContains(response, 'property="og:image" content="https://coappraiser.com/static/social/coappraiser-preflight-share.png"')
                self.assertContains(response, 'name="twitter:card" content="summary_large_image"')
                self.assertEqual(response.content.count(b'<meta name="description"'), 1)

    def test_non_public_account_page_is_not_indexed(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="robots" content="noindex,nofollow"')
        self.assertNotContains(response, '<link rel="canonical"')

    def test_home_includes_software_application_structured_data(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'type="application/ld+json"')
        self.assertContains(response, '"@type": "SoftwareApplication"')
        self.assertContains(response, '"audienceType": "Residential appraisers"')

    def test_robots_points_to_sitemap_and_protects_private_routes(self):
        response = self.client.get(reverse("robots"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertContains(response, "Disallow: /app/")
        self.assertContains(response, "Disallow: /accounts/")
        self.assertContains(response, "Disallow: /demo/reviews/")
        self.assertContains(response, "Sitemap: https://coappraiser.com/sitemap.xml")

    def test_sitemap_lists_only_canonical_public_pages(self):
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml; charset=utf-8")
        for path in ("/", "/demo/", "/faq/", "/pricing/", "/contact/", "/terms/"):
            self.assertContains(response, f"<loc>https://coappraiser.com{path}</loc>")
        self.assertNotContains(response, "/app/")
        self.assertNotContains(response, "/accounts/")

    def test_social_image_is_committed_at_expected_dimensions(self):
        import struct

        image_path = Path(settings.BASE_DIR) / "assets" / "social" / "coappraiser-preflight-share.png"
        self.assertTrue(image_path.exists())
        with image_path.open("rb") as image:
            header = image.read(24)
        self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", header[16:24]), (1200, 630))