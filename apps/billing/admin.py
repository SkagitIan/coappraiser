from django.contrib import admin
from .models import StripeEvent, Subscription
admin.site.register([Subscription, StripeEvent])
