from django import forms
from apps.catalog.models import Book, Copy


# Create the form class.
class ISBNCheckForm(forms.Form):
    isbn = forms.CharField(label="ISBN", max_length=13)


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

    def clean_isbn(self):
        isbn = self.cleaned_data["isbn"]
        # 重複チェックを無視して通す（ビューで処理）
        return isbn


class CopyForm(forms.ModelForm):
    class Meta:
        model = Copy
        fields = ["location", "status"]
