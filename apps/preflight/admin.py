from django.contrib import admin
from .models import FindingDecision, PreflightReview, ReviewFile, ReviewFinding, ReviewVersion, WorkfileReviewRecord

admin.site.register([PreflightReview, ReviewVersion, ReviewFile, ReviewFinding, FindingDecision, WorkfileReviewRecord])
