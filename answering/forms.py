from django import forms


class InputForm(forms.Form):
    subject = forms.CharField(label="Betreff")
    content = forms.CharField(widget=forms.Textarea, label="Inhalt")
