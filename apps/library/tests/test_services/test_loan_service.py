import datetime
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import Book, Copy, StorageLocation
from apps.library.models import LoanHistory, ReservationHistory
from apps.library.services.loan_service import LoanService

User = get_user_model()
LIBRARIAN = User.UserRole.LIBRARIAN
GENERAL = User.UserRole.GENERAL


@pytest.fixture
def general(db):
    return User.objects.create_user(username="gen", password="pass", role=GENERAL)


@pytest.fixture
def book(db):
    return Book.objects.create(
        isbn="1234567890123",
        title="Test Book",
        author="Author",
        publisher="Pub",
        published_date=datetime.date(2024, 1, 1),
        edition=1,
    )


@pytest.fixture
def location(db):
    return StorageLocation.objects.create(name="第1書庫")


@pytest.fixture
def copy(db, book, location):
    return Copy.objects.create(
        book=book,
        location=location,
        status=Copy.Status.AVAILABLE,
    )


@pytest.fixture
def copy_factory(db, book, location):
    def create_copy(**kwargs):
        return Copy.objects.create(
            book=book,
            location=location,
            status=Copy.Status.AVAILABLE,
            **kwargs,
        )

    return create_copy


@pytest.fixture
def today():
    return timezone.localdate()


@pytest.fixture
def due(today):
    return today + timedelta(days=7)


@pytest.mark.django_db(transaction=True)  # トランザクション対応のDBアクセスを許可
class TestLoanService:

    def test_can_borrow_more_true(self, general):
        assert LoanService.can_borrow_more(general) is True

    def test_can_borrow_more_false(self, general, copy, today, due, settings):
        settings.MAX_LOAN_COUNT = 1  # このsettingsはテスト専用のモック設定なので安全
        LoanHistory.objects.create(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=due,
            status=LoanHistory.Status.ON_LOAN,
        )
        assert LoanService.can_borrow_more(general) is False

    def test_loan_copy_success(self, general, copy, today, due):
        loan = LoanService.loan_copy(
            user=general, copy=copy, loan_date=today, due_date=due
        )
        assert loan.status == LoanHistory.Status.ON_LOAN
        copy.refresh_from_db()
        assert copy.status == Copy.Status.LOANED

    def test_loan_copy_succeeds_when_reservation_period_does_not_overlap(
        self, general, copy, today, due
    ):
        # 他人の予約が期間外
        other_user = User.objects.create_user(username="otheruser")
        ReservationHistory.objects.create(
            user=other_user,
            copy=copy,
            start_date=due + timedelta(days=1),  # 貸出期間の後
            end_date=due + timedelta(days=10),
            status=ReservationHistory.Status.RESERVED,
        )
        loan = LoanService.loan_copy(
            user=general, copy=copy, loan_date=today, due_date=due
        )
        assert loan.status == LoanHistory.Status.ON_LOAN

    def test_loan_copy_fails_when_user_reaches_max_loans(
        self, general, copy_factory, today, due, settings
    ):
        settings.MAX_LOAN_COUNT = 1
        # すでに1冊借りている
        LoanHistory.objects.create(
            user=general,
            copy=copy_factory(),
            loan_date=today,
            due_date=due,
            status=LoanHistory.Status.ON_LOAN,
        )
        with pytest.raises(ValidationError, match="貸出可能な上限に達しています"):
            LoanService.loan_copy(
                user=general, copy=copy_factory(), loan_date=today, due_date=due
            )

    def test_loan_copy_fails_when_copy_already_loaned(self, general, copy, today, due):
        copy.status = Copy.Status.LOANED
        copy.save()
        with pytest.raises(ValidationError, match="既に貸出中"):
            LoanService.loan_copy(
                user=general, copy=copy, loan_date=today, due_date=due
            )

    def test_loan_copy_fails_when_other_user_has_reservation(
        self, general, copy, today, due
    ):
        other_user = User.objects.create_user(username="otheruser")
        ReservationHistory.objects.create(
            user=other_user,
            copy=copy,
            start_date=today,
            end_date=due,
            status=ReservationHistory.Status.RESERVED,
        )
        with pytest.raises(ValidationError, match="予約が存在"):
            LoanService.loan_copy(
                user=general, copy=copy, loan_date=today, due_date=due
            )

    def test_loan_copy_completes_own_reservation(self, general, copy, today, due):
        ReservationHistory.objects.create(
            user=general,
            copy=copy,
            start_date=today,
            end_date=due,
            status=ReservationHistory.Status.RESERVED,
        )
        LoanService.loan_copy(user=general, copy=copy, loan_date=today, due_date=due)
        updated_res = ReservationHistory.objects.get(user=general, copy=copy)
        assert updated_res.status == ReservationHistory.Status.COMPLETED
