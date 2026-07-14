from django.db import models


class Lead(models.Model):
    KIND_CHOICES = [
        ("contact", "Contact message"),
        ("checklist", "UAD 3.6 checklist request"),
    ]

    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="contact")
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    message = models.TextField(blank=True)
    source_page = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.email}"
