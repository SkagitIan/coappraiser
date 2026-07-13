from django.conf import settings

PLANS = {
    "starter": {"name": "Starter", "price": "$39/month", "amount": 39, "price_id": settings.STRIPE_PRICE_STARTER, "description": "Revision drafting, basic QA support, and workfile notes."},
    "pro": {"name": "Pro", "price": "$99/month", "amount": 99, "price_id": settings.STRIPE_PRICE_PRO, "description": "Revision response, UAD issue review, market evidence, and workfile logging."},
    "elite": {"name": "Elite", "price": "$149/month", "amount": 149, "price_id": settings.STRIPE_PRICE_ELITE, "description": "Expanded QA workflows, templates, and evidence packaging."},
}

def get_plan(slug):
    return PLANS.get(slug)

