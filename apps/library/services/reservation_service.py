from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Copy
from apps.library.models import LoanHistory, ReservationHistory
from apps.library.services.loan_service import LoanService


class ReservationService:

    @classmethod
    def can_make_reservation(cls, user):
        max_reservations = settings.MAX_RESERVATION_COUNT
        current_reservations = ReservationHistory.objects.filter(
            user=user, status=ReservationHistory.Status.RESERVED
        ).count()
        return current_reservations < max_reservations

    @classmethod
    @transaction.atomic
    def reserve_copy(cls, user, copy, start_date, end_date):
        if not cls.can_make_reservation(user):
            raise ValidationError("予約可能な上限に達しています。")

        # 対象の蔵書をロック
        copy_locked = Copy.objects.select_for_update().get(pk=copy.pk)

        if copy_locked.status != Copy.Status.LOANED:
            raise ValidationError("貸出中の蔵書のみ予約可能です。")

        # 利用者自身の重複予約がないかチェック
        existing_user_reservation = (
            ReservationHistory.objects.select_for_update()
            .filter(
                copy=copy_locked,
                user=user,
                status=ReservationHistory.Status.RESERVED,
            )
            .exists()
        )
        if existing_user_reservation:
            raise ValidationError("同じ利用者が同じ蔵書で重複する予約はできません。")

        # 重複予約がないか確認
        overlapping = ReservationHistory.objects.select_for_update().filter(
            copy=copy_locked,
            status=ReservationHistory.Status.RESERVED,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        if overlapping.exists():
            raise ValidationError("この蔵書には、重複する予約がすでに存在します。")

        # 自分がその蔵書を貸出中かチェック
        user_on_loan = (
            LoanHistory.objects.select_for_update()
            .filter(
                copy=copy_locked,
                user=user,
                status=LoanHistory.Status.ON_LOAN,
            )
            .exists()
        )
        if user_on_loan:
            raise ValidationError("現在貸出中の蔵書は予約できません。")

        # 貸出中の期間と重複していないか確認（貸出中の期間が予約期間と重なるか）
        overlapping_loans = LoanHistory.objects.select_for_update().filter(
            copy=copy_locked,
            status=LoanHistory.Status.ON_LOAN,
            loan_date__lte=end_date,
            due_date__gte=start_date,
        )
        if overlapping_loans.exists():
            raise ValidationError("貸出中の期間と重複する予約はできません。")

        # 予約を保存
        reservation = ReservationHistory.objects.create(
            user=user,
            copy=copy_locked,
            start_date=start_date,
            end_date=end_date,
            status=ReservationHistory.Status.RESERVED,
        )
        return reservation

    @staticmethod
    @transaction.atomic
    def convert_to_loan(reservation, loan_date=None):
        if reservation.status != ReservationHistory.Status.RESERVED:
            raise ValidationError("予約中のものしか貸出にできません。")

        loan_date = loan_date or timezone.localdate()
        if loan_date < reservation.start_date:
            raise ValidationError("貸出日は予約開始日より前にはできません。")
        if loan_date > reservation.end_date:
            raise ValidationError("貸出日は予約終了日より後にはできません。")

        due_date = reservation.end_date
        loan = LoanService.loan_copy(
            user=reservation.user,
            copy=reservation.copy,
            loan_date=loan_date,
            due_date=due_date,
        )

        reservation.status = ReservationHistory.Status.COMPLETED
        reservation.save()

        return loan
