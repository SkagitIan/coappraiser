from django.conf import settings

PLANS = {
    "preflight": {"name": "Preflight", "price": "$59/month", "amount": 59, "price_id": getattr(settings, "STRIPE_PRICE_PREFLIGHT", ""), "description": "A focused pre-delivery review for independent residential appraisers.", "features": ["One free scan to start", "Completed XML, PDF, and photo package review", "Prioritized findings and revision comparison", "Workfile review record", "Cancel anytime"]},
}

def get_plan(slug):
    return PLANS.get(slug)
