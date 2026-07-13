from django.contrib import admin
from .models import OutputArtifact, VerificationItem
admin.site.register([OutputArtifact, VerificationItem])

