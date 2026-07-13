from django import forms
from .models import Assignment, Document

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "property_address", "assignment_type", "client_name", "effective_date"]
        widgets = {"effective_date": forms.DateInput(attrs={"type": "date"})}

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "document_type", "file", "pasted_text"]
        help_texts = {"pasted_text": "Paste source material here if you do not have a file."}

