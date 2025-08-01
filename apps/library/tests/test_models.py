from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import Copy
from apps.library.models import LoanHistory, ReservationHistory

User = get_user_model()


@pytest.mark.django_db
class TestLoanHistory:

    def setup_method(self):
        self.user = User.objects.create(username="testuser")
        self.copy = Copy.objects.create(title="Test Book", status=Copy.Status.AVAILABLE)
        self.today = timezone.now().date()
        self.due = self.today + timedelta(days=7)

    def test_can_borrow_more_true(self):
        assert LoanHistory.can_borrow_more(self.user) is True

    def test_can_borrow_more_false(self):
        settings.MAX_LOAN_COUNT = 1
        LoanHistory.objects.create(
            user=self.user,
            copy=self.copy,
            loan_date=self.today,
            due_date=self.due,
            status=LoanHistory.Status.ON_LOAN,
        )
        assert LoanHistory.can_borrow_more(self.user) is False

    def test_loan_copy_success(self):
        loan = LoanHistory.loan_copy(
            user=self.user, copy=self.copy, loan_date=self.today, due_date=self.due
        )
        assert loan.status == LoanHistory.Status.ON_LOAN
        self.copy.refresh_from_db()
        assert self.copy.status == Copy.Status.LOANED

    def test_loan_copy_fails_when_copy_already_loaned(self):
        self.copy.status = Copy.Status.LOANED
        self.copy.save()
        with pytest.raises(ValidationError, match="既に貸出中"):
            LoanHistory.loan_copy(
                user=self.user, copy=self.copy, loan_date=self.today, due_date=self.due
            )

    def test_loan_copy_fails_when_other_user_has_reservation(self):
        other_user = User.objects.create(username="otheruser")
        ReservationHistory.objects.create(
            user=other_user,
            copy=self.copy,
            start_date=self.today,
            end_date=self.due,
            status=ReservationHistory.Status.RESERVED,
        )
        with pytest.raises(ValidationError, match="予約が存在"):
            LoanHistory.loan_copy(
                user=self.user, copy=self.copy, loan_date=self.today, due_date=self.due
            )

    def test_loan_copy_completes_own_reservation(self):
        ReservationHistory.objects.create(
            user=self.user,
            copy=self.copy,
            start_date=self.today,
            end_date=self.due,
            status=ReservationHistory.Status.RESERVED,
        )
        LoanHistory.loan_copy(
            user=self.user, copy=self.copy, loan_date=self.today, due_date=self.due
        )
        updated_res = ReservationHistory.objects.get(user=self.user, copy=self.copy)
        assert updated_res.status == ReservationHistory.Status.COMPLETED

    def test_mark_returned_sets_status_and_date(self):
        loan = LoanHistory.objects.create(
            user=self.user,
            copy=self.copy,
            loan_date=self.today,
            due_date=self.due,
            status=LoanHistory.Status.ON_LOAN,
        )
        return_date = self.today + timedelta(days=5)
        loan.mark_returned(return_date=return_date)
        assert loan.status == LoanHistory.Status.RETURNED
        assert loan.return_date == return_date

    def test_clean_valid_dates(self):
        loan = LoanHistory(
            user=self.user,
            copy=self.copy,
            loan_date=self.today,
            due_date=self.today + timedelta(days=10),
        )
        loan.full_clean()  # Should not raise

    def test_clean_invalid_due_date(self):
        loan = LoanHistory(
            user=self.user,
            copy=self.copy,
            loan_date=self.today,
            due_date=self.today - timedelta(days=1),
        )
        with pytest.raises(ValidationError) as e:
            loan.full_clean()
        assert "due_date" in e.value.message_dict

    def test_clean_invalid_return_date(self):
        loan = LoanHistory(
            user=self.user,
            copy=self.copy,
            loan_date=self.today,
            due_date=self.due,
            return_date=self.today - timedelta(days=5),
        )
        with pytest.raises(ValidationError) as e:
            loan.full_clean()
        assert "return_date" in e.value.message_dict
