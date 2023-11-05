from django import forms


class SearchForm(forms.Form):
    query = forms.CharField()
    results = forms.IntegerField(initial=5)
