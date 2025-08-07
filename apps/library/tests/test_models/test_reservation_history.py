import datetime
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import Book, Copy, StorageLocation
from apps.library.models import ReservationHistory

User = get_user_model()
LIBRARIAN = User.UserRole.LIBRARIAN
GENERAL = User.UserRole.GENERAL


@pytest.fixture
def general_user(db):
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
class TestReservationHistory:

    def test_str_method(self, general_user, copy, today):
        reservation = ReservationHistory(
            user=general_user,
            copy=copy,
            start_date=today,
            end_date=today + timedelta(days=1),
        )
        expected_str = f"{general_user} - {copy} ({ReservationHistory.Status.RESERVED})"
        assert str(reservation) == expected_str

    def test_clean_valid_reservation(self, general_user, copy, today):
        reservation = ReservationHistory(
            user=general_user,
            copy=copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )
        reservation.full_clean()  # Should not raise

    def test_clean_start_date_before_today_raises(self, general_user, copy, today):
        reservation = ReservationHistory(
            user=general_user,
            copy=copy,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )
        with pytest.raises(ValidationError) as excinfo:
            reservation.full_clean()
        assert "予約開始日は本日以降の日付を指定してください。" in str(excinfo.value)

    def test_clean_start_date_after_max_start_date_raises(
        self, general_user, copy, today
    ):
        reservation = ReservationHistory(
            user=general_user,
            copy=copy,
            start_date=today + timedelta(days=91),
            end_date=today + timedelta(days=95),
            status=ReservationHistory.Status.RESERVED,
        )
        with pytest.raises(ValidationError) as excinfo:
            reservation.full_clean()
        assert "予約開始日は本日から3か月以内の日付を指定してください。" in str(
            excinfo.value
        )

    def test_clean_end_date_before_start_date_raises(self, general_user, copy, today):
        reservation = ReservationHistory(
            user=general_user,
            copy=copy,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )
        with pytest.raises(ValidationError) as excinfo:
            reservation.full_clean()
        assert "予約終了日は予約開始日以降の日付を指定してください。" in str(
            excinfo.value
        )

    def test_clean_reservation_period_exceeds_14_days_raises(
        self, general_user, copy, today
    ):
        reservation = ReservationHistory(
            user=general_user,
            copy=copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=16),
            status=ReservationHistory.Status.RESERVED,
        )
        with pytest.raises(ValidationError) as excinfo:
            reservation.full_clean()
        assert "予約期間は最大14日間までです。" in str(excinfo.value)

    def test_clean_non_reserved_status_skips_date_checks(
        self, general_user, copy, today
    ):
        reservation = ReservationHistory(
            user=general_user,
            copy=copy,
            start_date=today - timedelta(days=100),
            end_date=today - timedelta(days=90),
            status=ReservationHistory.Status.CANCELED,
        )
        reservation.full_clean()  # No exception expected

    def test_save_calls_full_clean(self, general_user, copy, today):
        reservation = ReservationHistory(
            user=general_user,
            copy=copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )
        reservation.save()
        assert ReservationHistory.objects.filter(pk=reservation.pk).exists()

    def test_cancel_changes_status(self, general_user, copy, today):
        reservation = ReservationHistory.objects.create(
            user=general_user,
            copy=copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )
        reservation.cancel()
        reservation.refresh_from_db()
        assert reservation.status == ReservationHistory.Status.CANCELED

    def test_cancel_raises_if_not_reserved(self, general_user, copy, today):
        reservation = ReservationHistory.objects.create(
            user=general_user,
            copy=copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.CANCELED,
        )
        with pytest.raises(ValidationError) as excinfo:
            reservation.cancel()
        assert "予約中のものしかキャンセルできません。" in str(excinfo.value)
