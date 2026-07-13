from django.urls import path
from . import views

app_name = "billing"
urlpatterns = [
    path("", views.billing_page, name="account"),
    path("pricing/", views.pricing, name="pricing"),
    path("start/", views.start_checkout, name="start_checkout"),
    path("checkout/", views.checkout, name="checkout"),
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
    path("portal/", views.portal, name="portal"),
    path("webhook/", views.webhook, name="webhook"),
]
