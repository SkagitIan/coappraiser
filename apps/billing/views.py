import json
import stripe
from urllib.parse import urlencode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Subscription
from .plans import PLANS, get_plan
from .services import process_event, stripe_client

def billing_mode():
    return settings.COAPPRAISER_BILLING_MODE

def has_active_subscription(user):
    if not user.is_authenticated:
        return False
    if billing_mode() == "mock":
        return True
    subscription = getattr(user, "subscription", None)
    return subscription is not None and subscription.is_active()

def subscription_required(view):
    def wrapped(request, *args, **kwargs):
        if not has_active_subscription(request.user):
            messages.info(request, "Choose a plan to use this workflow. Your account and billing settings remain available.")
            return redirect(f"{reverse('billing:pricing')}?{urlencode({'next': request.get_full_path()})}")
        return view(request, *args, **kwargs)
    wrapped.__name__ = view.__name__
    return login_required(wrapped)

def pricing(request):
    return render(request, "marketing/pricing.html", {"plans": PLANS, "next": request.GET.get("next", "")})

@login_required
def start_checkout(request):
    plan = get_plan(request.GET.get("plan"))
    if not plan:
        return redirect("billing:pricing")
    return render(request, "billing/confirm.html", {"plan": plan, "slug": request.GET.get("plan")})

@login_required
@require_POST
def checkout(request):
    plan_slug = request.POST.get("plan") or request.GET.get("plan")
    plan = get_plan(plan_slug)
    if not plan:
        return JsonResponse({"error": "Choose a valid CoAppraiser plan."}, status=400)
    if billing_mode() == "mock":
        sub, _ = Subscription.objects.get_or_create(user=request.user)
        sub.plan, sub.status = plan_slug, "active"
        sub.save(update_fields=["plan", "status", "updated_at"])
        return redirect("billing:success")
    if not settings.STRIPE_SECRET_KEY or not plan["price_id"]:
        messages.error(request, "Billing is not configured yet. Please try again later or contact CoAppraiser.")
        return redirect("billing:pricing")
    stripe_api = stripe_client()
    subscription = getattr(request.user, "subscription", None)
    customer_id = subscription.stripe_customer_id if subscription else ""
    try:
        if not customer_id:
            customer = stripe_api.Customer.create(email=request.user.email or None, metadata={"user_id": str(request.user.pk)})
            customer_id = customer.id
            Subscription.objects.update_or_create(user=request.user, defaults={"stripe_customer_id": customer_id})
        session = stripe_api.checkout.Session.create(mode="subscription", customer=customer_id, line_items=[{"price": plan["price_id"], "quantity": 1}], success_url=request.build_absolute_uri(reverse("billing:success")) + "?session_id={CHECKOUT_SESSION_ID}", cancel_url=request.build_absolute_uri(reverse("billing:cancel")), metadata={"user_id": str(request.user.pk), "plan": plan_slug}, subscription_data={"metadata": {"user_id": str(request.user.pk), "plan": plan_slug}})
    except stripe.error.StripeError:
        messages.error(request, "Stripe could not start checkout. Verify that this plan uses a recurring Price ID from the configured Stripe account and mode.")
        return redirect("billing:pricing")
    return redirect(session.url)

@login_required
def success(request):
    return render(request, "billing/success.html", {"pending": billing_mode() != "mock"})

def cancel(request):
    return render(request, "billing/cancel.html")

@login_required
def billing_page(request):
    return render(request, "billing/account.html", {"subscription": getattr(request.user, "subscription", None), "plans": PLANS})

@login_required
@require_POST
def portal(request):
    subscription = getattr(request.user, "subscription", None)
    if billing_mode() == "mock":
        messages.info(request, "Customer portal is available after Stripe is configured in this environment.")
        return redirect("billing:account")
    if not subscription or not subscription.stripe_customer_id or not settings.STRIPE_SECRET_KEY:
        messages.error(request, "No Stripe billing account is connected yet.")
        return redirect("billing:account")
    try:
        session = stripe_client().billing_portal.Session.create(customer=subscription.stripe_customer_id, return_url=request.build_absolute_uri(reverse("billing:account")))
    except stripe.error.StripeError:
        messages.error(request, "Stripe could not open the customer portal. Please try again after billing is connected.")
        return redirect("billing:account")
    return redirect(session.url)

@csrf_exempt
@require_POST
def webhook(request):
    payload = request.body
    signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe_client().Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
        elif settings.DEBUG and billing_mode() == "mock":
            event = json.loads(payload)
        else:
            return HttpResponse("Webhook is not configured", status=503)
        process_event(event)
    except Exception as exc:
        return HttpResponse(f"Invalid webhook: {exc}", status=400)
    return JsonResponse({"received": True})
