import json
from datetime import datetime, timezone as dt_timezone
from django.conf import settings
from django.contrib.auth.models import User
from .models import StripeEvent, Subscription

def stripe_client():
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe

def _timestamp(value):
    return datetime.fromtimestamp(int(value), tz=dt_timezone.utc) if value else None

def _value(obj, key, default=None):
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

def find_user(customer_id=None, metadata=None):
    user_id = (metadata or {}).get("user_id")
    if user_id:
        try:
            return User.objects.get(pk=int(user_id))
        except (User.DoesNotExist, ValueError):
            pass
    return User.objects.filter(subscription__stripe_customer_id=customer_id).first()

def sync_subscription(subscription_data, user=None):
    metadata = _value(subscription_data, "metadata", {}) or {}
    customer_id = _value(subscription_data, "customer", "") or ""
    user = user or find_user(customer_id, metadata)
    if not user:
        return None
    items = _value(subscription_data, "items", {}) or {}
    data = _value(items, "data", []) or []
    first_item = data[0] if data else {}
    price = _value(_value(first_item, "price", {}) or {}, "id", "")
    plan = metadata.get("plan", "")
    from .plans import PLANS
    if not plan:
        plan = next((slug for slug, config in PLANS.items() if config["price_id"] == price), "")
    sub, _ = Subscription.objects.get_or_create(user=user)
    sub.stripe_customer_id = customer_id or sub.stripe_customer_id
    sub.stripe_subscription_id = _value(subscription_data, "id", "") or sub.stripe_subscription_id
    sub.stripe_price_id = price or sub.stripe_price_id
    sub.plan = plan or sub.plan
    sub.status = _value(subscription_data, "status", "incomplete")
    sub.current_period_start = _timestamp(_value(subscription_data, "current_period_start"))
    sub.current_period_end = _timestamp(_value(subscription_data, "current_period_end"))
    sub.cancel_at_period_end = bool(_value(subscription_data, "cancel_at_period_end", False))
    sub.save()
    return sub

def mark_customer_past_due(customer_id):
    sub = Subscription.objects.filter(stripe_customer_id=customer_id).first()
    if sub:
        sub.status = "past_due"
        sub.save(update_fields=["status", "updated_at"])
    return sub

def process_event(event):
    event_id = _value(event, "id", "")
    event_type = _value(event, "type", "")
    if not event_id:
        raise ValueError("Stripe event is missing an ID.")
    if StripeEvent.objects.filter(event_id=event_id).exists():
        return False
    obj = _value(_value(event, "data", {}) or {}, "object", {}) or {}
    if event_type == "checkout.session.completed":
        customer = _value(obj, "customer", "")
        subscription_id = _value(obj, "subscription", "")
        metadata = _value(obj, "metadata", {}) or {}
        if subscription_id:
            try:
                subscription_data = stripe_client().Subscription.retrieve(subscription_id)
            except Exception:
                subscription_data = {"id": subscription_id, "customer": customer, "metadata": metadata, "status": "active"}
            sync_subscription(subscription_data)
    elif event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
        sync_subscription(obj)
    elif event_type == "invoice.payment_failed":
        mark_customer_past_due(_value(obj, "customer", ""))
    StripeEvent.objects.create(event_id=event_id, event_type=event_type, payload=json.loads(json.dumps(event, default=str)))
    return True
