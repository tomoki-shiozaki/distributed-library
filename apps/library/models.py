from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
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

    def __str__(self):
        return f"{self.user} - {self.copy} ({self.status})"

    def clean(self):
        errors = {}

        # 日付チェック: loan_date <= due_date <= loan_date + 14日
        if self.due_date and self.loan_date:
            if self.due_date < self.loan_date:
                errors["due_date"] = "返却予定日は貸出日以降の日付を指定してください。"
            elif self.due_date > self.loan_date + timedelta(days=14):
                errors["due_date"] = (
                    "返却予定日は貸出日から14日以内の日付を指定してください。"
                )

        # 返却日がある場合のバリデーション
        if self.return_date:
            if self.return_date < self.loan_date:
                errors["return_date"] = "返却日は貸出日以降の日付を指定してください。"
            elif self.return_date > timezone.localdate():
                errors["return_date"] = "返却日は今日以前の日付を指定してください。"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def mark_returned(self, return_date=None):
        """
        返却処理用のヘルパーメソッド。
        - 返却日を設定
        - ステータスを「返却済み」に変更
        - 関連する Copy を AVAILABLE に更新
        """
        self.return_date = return_date or timezone.localdate()
        self.status = self.Status.RETURNED
        self.save()

        # Copy 状態更新
        self.copy.status = Copy.Status.AVAILABLE
        self.copy.save()

    class Meta:
        verbose_name = "貸出履歴"
        verbose_name_plural = "貸出履歴"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["copy"]),
            models.Index(fields=["status"]),
        ]


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

    def __str__(self):
        return f"{self.user} - {self.copy} ({self.status})"

    def clean(self):
        super().clean()

        # 予約中の場合のみ日付チェックを厳格に行う
        if self.status == self.Status.RESERVED:
            today = timezone.localdate()
            max_start_date = today + timedelta(days=90)

            if self.start_date < today:
                raise ValidationError(
                    _("予約開始日は本日以降の日付を指定してください。")
                )

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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def cancel(self):
        if self.status != self.Status.RESERVED:
            raise ValidationError("予約中のものしかキャンセルできません。")
        self.status = self.Status.CANCELED
        self.save()

    class Meta:
        verbose_name = "予約履歴"
        verbose_name_plural = "予約履歴"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["copy"]),
            models.Index(fields=["status"]),
        ]
