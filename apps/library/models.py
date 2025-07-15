from datetime import date, timedelta

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Copy

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
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, verbose_name="蔵書")
    start_date = models.DateField(verbose_name="予約開始日")
    end_date = models.DateField(verbose_name="予約終了日")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.RESERVED,
        verbose_name="ステータス",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="予約作成日")

    def clean(self):
        super().clean()

        today = date.today()
        max_start_date = today + timedelta(days=90)

        if self.start_date < today:
            raise ValidationError(_("予約開始日は本日以降の日付を指定してください。"))

        if self.start_date > max_start_date:
            raise ValidationError(
                _("予約開始日は本日から3か月以内の日付を指定してください。")
            )

        # 開始日より終了日が前
        if self.end_date < self.start_date:
            raise ValidationError(
                _("予約終了日は予約開始日以降の日付を指定してください。")
            )

        # 最大期間2週間以内
        if self.end_date - self.start_date > timedelta(days=14):
            raise ValidationError(_("予約期間は最大14日間までです。"))

        # 予約重複チェック
        overlapping = ReservationHistory.objects.filter(
            copy=self.copy,
            status=ReservationHistory.Status.RESERVED,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
        ).exclude(id=self.id)
        if overlapping.exists():
            raise ValidationError(_("この蔵書には、重複する予約がすでに存在します。"))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "予約履歴"
        verbose_name_plural = "予約履歴"

    def __str__(self):
        return f"{self.user} - {self.copy} ({self.status})"
