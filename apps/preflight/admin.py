from django.contrib import admin
from .models import AIExecution, ExtractedObservation, FindingDecision, PreflightReview, ReviewFile, ReviewFinding, ReviewVersion, WorkfileReviewRecord

admin.site.register([PreflightReview, ReviewVersion, ReviewFile, ExtractedObservation, AIExecution, ReviewFinding, FindingDecision, WorkfileReviewRecord])
