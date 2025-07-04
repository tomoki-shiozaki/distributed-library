from django import forms


class BookSearchForm(forms.Form):
    q = forms.CharField(label="キーワード", required=False)
