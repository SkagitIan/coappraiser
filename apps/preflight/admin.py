from django.contrib import admin
from .models import ExtractedObservation, FindingDecision, PreflightReview, ReviewFile, ReviewFinding, ReviewVersion, WorkfileReviewRecord

admin.site.register([PreflightReview, ReviewVersion, ReviewFile, ExtractedObservation, ReviewFinding, FindingDecision, WorkfileReviewRecord])
