import json
from unittest.mock import patch, Mock
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from apps.assignments.models import Assignment
from .models import StripeEvent, Subscription
from .plans import PLANS

class BillingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("subscriber", password="pass12345", email="subscriber@example.com")

    def test_public_pricing_shows_preflight_plan(self):
        response = self.client.get(reverse("pricing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preflight")
        self.assertContains(response, PLANS["preflight"]["price"])

    def test_checkout_requires_login(self):
        response = self.client.get(reverse("billing:start_checkout") + "?plan=preflight")
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('billing:start_checkout')}%3Fplan%3Dpreflight")

    def test_mock_checkout_creates_active_subscription(self):
        self.client.login(username="subscriber", password="pass12345")
        response = self.client.post(reverse("billing:checkout"), {"plan": "preflight"})
        self.assertRedirects(response, reverse("billing:success"))
        subscription = Subscription.objects.get(user=self.user)
        self.assertEqual(subscription.plan, "preflight")
        self.assertEqual(subscription.status, "active")

    def test_signup_to_plan_to_mock_checkout_flow(self):
        signup = self.client.post(reverse("accounts:signup"), {"username": "newsubscriber", "email": "new@example.com", "password": "safe-pass-123"})
        self.assertRedirects(signup, reverse("preflight:dashboard"))
        pricing = self.client.get(reverse("pricing"))
        self.assertContains(pricing, reverse("accounts:signup"))
        confirm = self.client.get(reverse("billing:start_checkout") + "?plan=preflight")
        self.assertEqual(confirm.status_code, 200)
        checkout = self.client.post(reverse("billing:checkout"), {"plan": "preflight"})
        self.assertRedirects(checkout, reverse("billing:success"))

    def test_invalid_plan_is_rejected(self):
        self.client.login(username="subscriber", password="pass12345")
        response = self.client.post(reverse("billing:checkout"), {"plan": "tampered"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    @override_settings(COAPPRAISER_BILLING_MODE="stripe", STRIPE_SECRET_KEY="sk_test_configured")
    @patch("apps.billing.views.get_plan")
    @patch("apps.billing.views.stripe_client")
    def test_stripe_checkout_uses_server_side_price(self, stripe_client_mock, get_plan_mock):
        get_plan_mock.return_value = {"name": "Preflight", "price": "$59/month", "price_id": "price_server_preflight"}
        stripe = Mock()
        stripe.Customer.create.return_value = Mock(id="cus_server")
        stripe.checkout.Session.create.return_value = Mock(url="https://checkout.stripe.test/session")
        stripe_client_mock.return_value = stripe
        self.client.login(username="subscriber", password="pass12345")
        response = self.client.post(reverse("billing:checkout"), {"plan": "preflight"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://checkout.stripe.test/session")
        kwargs = stripe.checkout.Session.create.call_args.kwargs
        self.assertEqual(kwargs["line_items"][0]["price"], "price_server_preflight")
        self.assertEqual(kwargs["metadata"]["user_id"], str(self.user.pk))

    @override_settings(DEBUG=True, COAPPRAISER_BILLING_MODE="mock", STRIPE_WEBHOOK_SECRET="")
    def test_mock_webhook_is_idempotent_and_syncs_subscription(self):
        event = {"id": "evt_test_1", "type": "customer.subscription.updated", "data": {"object": {"id": "sub_test_1", "customer": "cus_test_1", "status": "active", "metadata": {"user_id": str(self.user.pk), "plan": "preflight"}, "items": {"data": [{"price": {"id": "price_test"}}]}, "current_period_start": 1700000000, "current_period_end": 1702600000, "cancel_at_period_end": False}}}
        first = self.client.post(reverse("billing:webhook"), data=json.dumps(event), content_type="application/json")
        second = self.client.post(reverse("billing:webhook"), data=json.dumps(event), content_type="application/json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(StripeEvent.objects.count(), 1)
        self.assertEqual(Subscription.objects.get(user=self.user).status, "active")

    @override_settings(DEBUG=False, COAPPRAISER_BILLING_MODE="stripe", STRIPE_WEBHOOK_SECRET="whsec_configured")
    def test_webhook_rejects_missing_signature(self):
        response = self.client.post(reverse("billing:webhook"), data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @override_settings(COAPPRAISER_BILLING_MODE="stripe")
    def test_unsubscribed_user_is_sent_to_plans_for_paid_workflow(self):
        assignment = Assignment.objects.create(user=self.user, title="Paid workflow")
        self.client.login(username="subscriber", password="pass12345")
        response = self.client.get(reverse("ai_tools:revision_response", args=[assignment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("billing:pricing"), response["Location"])

    @override_settings(COAPPRAISER_BILLING_MODE="stripe")
    def test_past_due_user_keeps_billing_access_but_not_paid_workflows(self):
        Subscription.objects.create(user=self.user, status="past_due", plan="preflight")
        self.client.login(username="subscriber", password="pass12345")
        billing = self.client.get(reverse("billing:account"))
        self.assertEqual(billing.status_code, 200)
        assignment = Assignment.objects.create(user=self.user, title="Past due workflow")
        workflow = self.client.get(reverse("ai_tools:revision_response", args=[assignment.pk]))
        self.assertEqual(workflow.status_code, 302)
        self.assertIn(reverse("billing:pricing"), workflow["Location"])
