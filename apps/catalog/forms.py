from django import forms
from django.core.validators import RegexValidator


# Create the form class.
class ISBNCheckForm(forms.Form):
    isbn = forms.CharField(
        label="ISBN",
        max_length=13,
        help_text="13桁の数字をハイフンなしで入力してください。",
        validators=[
            RegexValidator(
                regex=r"^\d{13}$",
                message="ISBNは13桁の数字で入力してください（ハイフンなし）。",
            )
        ],
    )
