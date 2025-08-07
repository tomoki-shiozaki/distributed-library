import datetime
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import Book, Copy, StorageLocation
from apps.library.models import LoanHistory, ReservationHistory

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
def today():
    return timezone.now().date()


@pytest.fixture
def due(today):
    return today + timedelta(days=7)


@pytest.mark.django_db
class TestLoanHistory:

    def test_mark_returned_sets_status_and_date(self, general, copy, today, due):
        loan = LoanHistory.objects.create(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=due,
            status=LoanHistory.Status.ON_LOAN,
        )
        return_date = today
        loan.mark_returned(return_date=return_date)

        assert loan.status == LoanHistory.Status.RETURNED
        assert loan.return_date == return_date

        copy.refresh_from_db()
        assert copy.status == Copy.Status.AVAILABLE

    def test_clean_valid_dates(self, general, copy, today):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=today + timedelta(days=10),
        )
        loan.full_clean()  # Should not raise

    def test_clean_due_date_max_boundary(self, general, copy, today):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=today + timedelta(days=14),
        )
        loan.full_clean()

    def test_clean_return_date_after_loan_date_valid(self, general, copy, today):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today - timedelta(days=3),
            due_date=today + timedelta(days=7),
            return_date=today - timedelta(days=2),  # 貸出日の翌日
        )
        loan.full_clean()

    def test_clean_return_date_today_is_valid(self, general, copy, today, due):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=due,
            return_date=today,
        )
        loan.full_clean()

    def test_clean_invalid_due_date(self, general, copy, today):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=today - timedelta(days=1),
        )
        with pytest.raises(ValidationError) as e:
            loan.full_clean()
        assert "due_date" in e.value.message_dict

    def test_clean_due_date_exceeds_max_days(self, general, copy, today):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=today + timedelta(days=15),  # 14日を超える
        )
        with pytest.raises(ValidationError) as e:
            loan.full_clean()
        assert "due_date" in e.value.message_dict

    def test_clean_invalid_return_date(self, general, copy, today, due):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=due,
            return_date=today - timedelta(days=5),
        )
        with pytest.raises(ValidationError) as e:
            loan.full_clean()
        assert "return_date" in e.value.message_dict

    def test_clean_return_date_in_future_is_invalid(self, general, copy, today, due):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=due,
            return_date=today + timedelta(days=1),  # 今日より未来
        )
        with pytest.raises(ValidationError) as e:
            loan.full_clean()
        assert "return_date" in e.value.message_dict

    def test_save_triggers_validation(self, general, copy, today):
        loan = LoanHistory(
            user=general,
            copy=copy,
            loan_date=today,
            due_date=today - timedelta(days=1),  # 不正
        )
        with pytest.raises(ValidationError):
            loan.save()
