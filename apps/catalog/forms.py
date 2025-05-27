from django import forms
from apps.catalog.models import Book, Copy


# Create the form class.
class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "author",
            "publisher",
            "published_date",
            "image_url",
            "edition",
        ]


class CopyForm(forms.ModelForm):
    class Meta:
        model = Copy
        fields = ["location", "status"]
