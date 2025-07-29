from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

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
        fields = ["loan_date", "due_date"]
        help_texts = {
            "due_date": "返却予定日は貸出日（本日）から14日以内の日付を指定してください。",
        }
        widgets = {
            "loan_date": forms.HiddenInput(),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.today = kwargs.pop("today")
        super().__init__(*args, **kwargs)

    def clean_loan_date(self):
        value = self.cleaned_data.get("loan_date")
        if value != self.today:
            raise forms.ValidationError("貸出日は今日以外にできません。")
        return value


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
