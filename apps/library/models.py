from django.db import models
from django.contrib.auth import get_user_model

from apps.catalog.models import Book, Copy

User = get_user_model()


# Create your models here.
class LoanHistory(models.Model):
    class Status(models.TextChoices):
        ON_LOAN = "on_loan", "貸出中"
        RETURNED = "returned", "返却済み"

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="利用者")
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, verbose_name="蔵書")
    loan_date = models.DateField(verbose_name="貸出日")
    due_date = models.DateField(verbose_name="返却予定日")
    return_date = models.DateField(null=True, blank=True, verbose_name="返却日")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ON_LOAN,
        verbose_name="ステータス",
    )

    class Meta:
        verbose_name = "貸出履歴"
        verbose_name_plural = "貸出履歴"

    def __str__(self):
        return f"{self.user} - {self.copy} ({self.status})"


class ReservationHistory(models.Model):
    class Status(models.TextChoices):
        RESERVED = "reserved", "予約中"
        CANCELED = "canceled", "キャンセル"
        COMPLETED = "completed", "完了"

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="利用者")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="本")
    start_date = models.DateField(verbose_name="予約開始日")
    end_date = models.DateField(verbose_name="予約終了日")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.RESERVED,
        verbose_name="ステータス",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="予約作成日")

    class Meta:
        verbose_name = "予約履歴"
        verbose_name_plural = "予約履歴"

    def __str__(self):
        return f"{self.user} - {self.book} ({self.status})"
