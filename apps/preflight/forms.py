from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super().clean(item, initial) for item in data]


class PreflightReviewForm(forms.Form):
    title = forms.CharField(max_length=200, label="Review name", help_text="Use a short name you will recognize in your review history.")
    subject_identifier = forms.CharField(max_length=300, required=False, label="Subject or file identifier", help_text="Optional address or internal identifier.")
    files = MultipleFileField(widget=MultipleFileInput(attrs={"multiple": True}), label="Completed appraisal package", help_text="Upload a UAD ZIP, or separate XML, PDF, images, and optional SSR files.")
    appraiser_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Optional appraiser note")
