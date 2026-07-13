from django import forms
class RevisionResponseForm(forms.Form):
    revision_request = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}), help_text="Paste the reviewer, lender, AMC, or client request exactly as received.")
    report_excerpt = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 5}), help_text="Optional relevant report language or grid excerpt.")
    appraiser_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 5}), help_text="Optional notes about the analysis or support you already have.")

class UADIssueForm(forms.Form):
    issue_text = forms.CharField(widget=forms.Textarea(attrs={"rows": 7}), help_text="Paste the UAD issue, validation-style message, or relevant report text.")

class MarketEvidenceForm(forms.Form):
    csv_file = forms.FileField(help_text="Upload an MLS CSV export. CoAppraiser will show the detected columns before using the summary.")
    appraiser_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}), help_text="Optional context about the market segment or effective date.")
