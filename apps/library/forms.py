from django import forms

from apps.library.models import LoanHistory, ReservationHistory


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


class LoanForm(forms.ModelForm):
    class Meta:
        model = LoanHistory
        fields = ["due_date"]
        help_texts = {
            "due_date": "返却予定日は貸出日（本日）から14日以内の日付を指定してください。",
        }
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = ReservationHistory
        fields = ["start_date", "end_date"]
        help_texts = {
            "start_date": "予約は本日以降の日付を指定してください。",
            "end_date": "予約期間は最長14日間です。",
        }
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
