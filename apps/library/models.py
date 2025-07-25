from datetime import timedelta

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
    loan_date = models.DateField(default=timezone.now, verbose_name="貸出日")
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

    @classmethod
    def loan_copy(cls, user, copy, loan_date, due_date):
        if not cls.can_borrow_more(user):
            raise ValidationError("貸出可能な上限に達しています。")

        with transaction.atomic():
            # 蔵書ロック
            copy_locked = Copy.objects.select_for_update().get(pk=copy.pk)

            if copy_locked.status == Copy.Status.LOANED:
                raise ValidationError("この蔵書は既に貸出中です。")

            # 予約チェック
            overlapping_reservation = ReservationHistory.objects.filter(
                copy=copy_locked,
                status=ReservationHistory.Status.RESERVED,
                start_date__lte=due_date,
                end_date__gte=loan_date,
            ).exclude(user=user)
            if overlapping_reservation.exists():
                raise ValidationError(
                    "他の利用者による予約が存在するため、貸出できません。"
                )

            # 貸出履歴作成
            loan_history = cls.objects.create(
                user=user,
                copy=copy_locked,
                loan_date=loan_date,
                due_date=due_date,
                status=cls.Status.ON_LOAN,
            )

            # 蔵書の状態更新
            copy_locked.status = Copy.Status.LOANED
            copy_locked.save()

            return loan_history

    @classmethod
    def can_borrow_more(cls, user):
        max_borrow = 5
        current_loans = cls.objects.filter(user=user, status=cls.Status.ON_LOAN).count()
        return current_loans < max_borrow

    def mark_returned(self, return_date=None):
        """
        返却処理用のヘルパーメソッド。
        引数がなければ今日を返却日に設定。
        statusを返却済みに更新し、保存する。
        """
        self.return_date = return_date or timezone.now().date()
        self.status = self.Status.RETURNED
        self.save()

    def clean(self):
        super().clean()

        # 貸出日 <= 返却予定日 <= 貸出日 + 14日
        if self.due_date < self.loan_date:
            raise ValidationError(_("返却予定日は貸出日以降の日付を指定してください。"))
        if self.due_date > self.loan_date + timedelta(days=14):
            raise ValidationError(
                _("返却予定日は貸出日から14日以内の日付を指定してください。")
            )

        # 返却日がある場合、貸出日 <= 返却日 <= 今日
        if self.return_date:
            if self.return_date < self.loan_date:
                raise ValidationError("返却日は貸出日以降の日付を指定してください。")
            if self.return_date > timezone.now().date():
                raise ValidationError("返却日は今日以前の日付を指定してください。")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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

    @classmethod
    def reserve_copy(cls, user, copy, start_date, end_date):
        if not cls.can_make_reservation(user):
            raise ValidationError("予約可能な上限に達しています。")

        with transaction.atomic():
            # 対象の蔵書をロック
            copy_locked = Copy.objects.select_for_update().get(pk=copy.pk)

            if copy_locked.status != Copy.Status.LOANED:
                raise ValidationError("貸出中の蔵書のみ予約可能です。")

            # 重複予約がないか確認
            overlapping = (
                cls.objects.select_for_update()
                .filter(
                    copy=copy_locked,
                    status=cls.Status.RESERVED,
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                )
                .exclude(user=user)
            )
            if overlapping.exists():
                raise ValidationError("この蔵書には、重複する予約がすでに存在します。")

            # 予約を保存
            reservation = cls.objects.create(
                user=user,
                copy=copy_locked,
                start_date=start_date,
                end_date=end_date,
                status=cls.Status.RESERVED,
            )
            return reservation

    @classmethod
    def can_make_reservation(cls, user):
        max_reservations = 3
        current_reservations = cls.objects.filter(
            user=user, status=cls.Status.RESERVED
        ).count()
        return current_reservations < max_reservations

    def clean(self):
        super().clean()

        today = timezone.now().date()
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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def cancel(self):
        if self.status != self.Status.RESERVED:
            raise ValidationError("予約中のものしかキャンセルできません。")
        self.status = self.Status.CANCELED
        self.save()

    def convert_to_loan(self, loan_date=None):
        if self.status != self.Status.RESERVED:
            raise ValidationError("予約中のものしか貸出にできません。")

        loan_date = loan_date or timezone.now().date()
        if loan_date > self.end_date:
            raise ValidationError("貸出日は予約終了日より後にはできません。")
        due_date = self.end_date
        loan = LoanHistory.loan_copy(
            user=self.user,
            copy=self.copy,
            loan_date=loan_date,
            due_date=due_date,
        )

        self.status = self.Status.COMPLETED
        self.save()

        return loan

    class Meta:
        verbose_name = "予約履歴"
        verbose_name_plural = "予約履歴"
