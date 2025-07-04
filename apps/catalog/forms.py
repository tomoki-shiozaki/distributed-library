from django import forms


# Create the form class.
class ISBNCheckForm(forms.Form):
    isbn = forms.CharField(label="ISBN", max_length=13)
