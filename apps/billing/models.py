from django.conf import settings
from django.db import models

class Subscription(models.Model):
    STATUS_CHOICES = [("incomplete", "Incomplete"), ("trialing", "Trialing"), ("active", "Active"), ("past_due", "Past due"), ("unpaid", "Unpaid"), ("canceled", "Canceled"), ("expired", "Expired")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription")
    stripe_customer_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    stripe_price_id = models.CharField(max_length=100, blank=True)
    plan = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="incomplete")
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def is_active(self):
        return self.status in {"active", "trialing"}

class StripeEvent(models.Model):
    event_id = models.CharField(max_length=120, unique=True)
    event_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(auto_now_add=True)

