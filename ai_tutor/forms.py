from django import forms


class AIChatForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)
