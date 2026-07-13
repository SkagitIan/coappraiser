from django.conf import settings

PLANS = {
    "starter": {"name": "Starter", "price": "$39/month", "amount": 39, "price_id": settings.STRIPE_PRICE_STARTER, "description": "A focused starting point for solo appraisers handling recurring revision work.", "features": ["Revision Response Agent", "Workfile notes and verification items", "Saved AI action history"]},
    "pro": {"name": "Pro", "price": "$99/month", "amount": 99, "price_id": settings.STRIPE_PRICE_PRO, "description": "The complete everyday copilot for revision response, readiness review, and evidence support.", "features": ["Everything in Starter", "UAD 3.6 Readiness Review", "Market Evidence Pack", "Unlimited assignment workspaces"]},
    "elite": {"name": "Elite", "price": "$149/month", "amount": 149, "price_id": settings.STRIPE_PRICE_ELITE, "description": "Expanded support for appraisers and small offices building a consistent review process.", "features": ["Everything in Pro", "Expanded QA and evidence packaging", "Priority workflow improvements", "Designed for office-level consistency"]},
}

def get_plan(slug):
    return PLANS.get(slug)
