from django import forms

from apps.library.models import ReservationHistory


class BookSearchForm(forms.Form):
    title = forms.CharField(label="タイトル", required=False)
    author = forms.CharField(label="著者名", required=False)
    publisher = forms.CharField(label="出版社", required=False)
    isbn = forms.CharField(
        label="ISBN",
        required=False,
        max_length=13,
        help_text="13桁の数字をハイフンなしで入力してください。",
    )


class ReservationForm(forms.ModelForm):
    class Meta:
        model = ReservationHistory
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
