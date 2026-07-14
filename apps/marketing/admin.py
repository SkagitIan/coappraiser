from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("email", "kind", "name", "source_page", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("email", "name", "message")
