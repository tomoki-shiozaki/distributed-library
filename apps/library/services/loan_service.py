from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Copy
from apps.library.models import LoanHistory, ReservationHistory


class LoanService:

    @classmethod
    def can_borrow_more(cls, user):
        max_borrow = settings.MAX_LOAN_COUNT
        current_loans = LoanHistory.objects.filter(
            user=user, status=LoanHistory.Status.ON_LOAN
        ).count()
        return current_loans < max_borrow

    @classmethod
    @transaction.atomic
    def loan_copy(cls, user, copy, loan_date, due_date):
        if not cls.can_borrow_more(user):
            raise ValidationError("貸出可能な上限に達しています。")

        # 蔵書ロック
        copy_locked = Copy.objects.select_for_update().get(pk=copy.pk)

        if copy_locked.status == Copy.Status.LOANED:
            raise ValidationError("この蔵書は既に貸出中です。")

        # 予約チェック（他人の予約があるか）
        overlapping_reservation = (
            ReservationHistory.objects.select_for_update()
            .filter(
                copy=copy_locked,
                status=ReservationHistory.Status.RESERVED,
                start_date__lte=due_date,
                end_date__gte=loan_date,
            )
            .exclude(user=user)
        )
        if overlapping_reservation.exists():
            raise ValidationError(
                "他の利用者による予約が存在するため、貸出できません。"
            )

        # 利用者自身の予約がある場合、貸出により予約は実質完了とみなし、状態を更新する
        user_reservations = ReservationHistory.objects.select_for_update().filter(
            copy=copy_locked,
            user=user,
            status=ReservationHistory.Status.RESERVED,
        )
        for reservation in user_reservations:
            reservation.status = ReservationHistory.Status.COMPLETED
            reservation.save()

        # 貸出履歴作成
        loan_history = LoanHistory.objects.create(
            user=user,
            copy=copy_locked,
            loan_date=loan_date,
            due_date=due_date,
            status=LoanHistory.Status.ON_LOAN,
        )

        # 蔵書状態更新
        copy_locked.status = Copy.Status.LOANED
        copy_locked.save()

        return loan_history
