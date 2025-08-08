import datetime
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import Book, Copy, StorageLocation
from apps.library.models import LoanHistory, ReservationHistory
from apps.library.services.reservation_service import ReservationService

User = get_user_model()
LIBRARIAN = User.UserRole.LIBRARIAN
GENERAL = User.UserRole.GENERAL


@pytest.fixture
def general_user(db):
    return User.objects.create_user(username="gen", password="pass", role=GENERAL)


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="otheruser", password="pass", role=GENERAL)


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


@pytest.fixture
def reserved_copy(copy):
    copy.status = Copy.Status.LOANED
    copy.save()
    return copy


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
def loaned_copy_factory(copy_factory):
    def _factory(**kwargs):
        # copy_factoryでcopyを作成し、状態だけLOANEDにする
        copy = copy_factory(**kwargs)
        copy.status = Copy.Status.LOANED
        copy.save()
        return copy

    return _factory


@pytest.mark.django_db(transaction=True)
class TestReservationService:

    def test_reservation_fails_if_user_exceeds_limit(
        self, general_user, loaned_copy_factory, today, settings
    ):
        settings.MAX_RESERVATION_COUNT = 1

        # 既に予約が1件ある場合（予約対象は貸出中状態のコピー）
        reserved_copy = loaned_copy_factory()
        ReservationHistory.objects.create(
            user=general_user,
            copy=reserved_copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.reserve_copy(
                user=general_user,
                copy=reserved_copy,
                start_date=today + timedelta(days=10),
                end_date=today + timedelta(days=14),
            )

        assert "予約可能な上限に達しています。" in str(excinfo.value)

    def test_reservation_fails_if_copy_not_loaned(self, general_user, copy, today):
        # 貸出中でない蔵書
        copy.status = Copy.Status.AVAILABLE
        copy.save()

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.reserve_copy(
                user=general_user,
                copy=copy,
                start_date=today + timedelta(days=1),
                end_date=today + timedelta(days=5),
            )
        assert "貸出中の蔵書のみ予約可能です。" in str(excinfo.value)

    def test_duplicate_reservation_by_same_user_fails(
        self, general_user, reserved_copy, today
    ):
        ReservationHistory.objects.create(
            user=general_user,
            copy=reserved_copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.reserve_copy(
                user=general_user,
                copy=reserved_copy,
                start_date=today + timedelta(days=2),
                end_date=today + timedelta(days=6),
            )
        assert "同じ利用者が同じ蔵書で重複する予約はできません。" in str(excinfo.value)

    def test_overlapping_reservations_fail(
        self, general_user, other_user, reserved_copy, today
    ):
        ReservationHistory.objects.create(
            user=other_user,
            copy=reserved_copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.reserve_copy(
                user=general_user,
                copy=reserved_copy,
                start_date=today + timedelta(days=3),
                end_date=today + timedelta(days=6),
            )
        assert "この蔵書には、重複する予約がすでに存在します。" in str(excinfo.value)

    def test_user_cannot_reserve_loaned_copy_they_hold(
        self, general_user, reserved_copy, today
    ):
        LoanHistory.objects.create(
            user=general_user,
            copy=reserved_copy,
            loan_date=today - timedelta(days=5),
            due_date=today + timedelta(days=5),
            status=LoanHistory.Status.ON_LOAN,
        )

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.reserve_copy(
                user=general_user,
                copy=reserved_copy,
                start_date=today + timedelta(days=1),
                end_date=today + timedelta(days=7),
            )
        assert "現在貸出中の蔵書は予約できません。" in str(excinfo.value)

    def test_overlapping_loan_period_fails(
        self, general_user, reserved_copy, other_user, today
    ):
        LoanHistory.objects.create(
            user=other_user,
            copy=reserved_copy,
            loan_date=today,
            due_date=today + timedelta(days=5),
            status=LoanHistory.Status.ON_LOAN,
        )

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.reserve_copy(
                user=general_user,
                copy=reserved_copy,
                start_date=today + timedelta(days=2),
                end_date=today + timedelta(days=7),
            )
        assert "貸出中の期間と重複する予約はできません。" in str(excinfo.value)

    def test_successful_reservation(self, general_user, reserved_copy, today):
        reservation = ReservationService.reserve_copy(
            user=general_user,
            copy=reserved_copy,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=12),
        )

        assert reservation.pk is not None
        assert reservation.user == general_user
        assert reservation.copy == reserved_copy
        assert reservation.status == ReservationHistory.Status.RESERVED


@pytest.mark.django_db(transaction=True)
class TestConvertToLoan:

    def test_convert_fails_if_not_reserved(self, general_user, reserved_copy, today):
        reservation = ReservationHistory.objects.create(
            user=general_user,
            copy=reserved_copy,
            start_date=today,
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.CANCELED,
        )

        with pytest.raises(ValidationError) as excinfo:
            ReservationService.convert_to_loan(reservation)
        assert "予約中のものしか貸出にできません。" in str(excinfo.value)

    def test_convert_fails_if_loan_date_out_of_range(
        self, general_user, reserved_copy, today
    ):
        reservation = ReservationHistory.objects.create(
            user=general_user,
            copy=reserved_copy,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )

        with pytest.raises(ValidationError):
            ReservationService.convert_to_loan(reservation, loan_date=today)

    def test_convert_successfully(self, mocker, general_user, reserved_copy, today):
        reservation = ReservationHistory.objects.create(
            user=general_user,
            copy=reserved_copy,
            start_date=today,
            end_date=today + timedelta(days=5),
            status=ReservationHistory.Status.RESERVED,
        )

        mock_loan = mocker.MagicMock()
        mock_loan.pk = 999
        mocker.patch(
            "apps.library.services.loan_service.LoanService.loan_copy",
            return_value=mock_loan,
        )

        loan = ReservationService.convert_to_loan(reservation, loan_date=today)

        assert loan.pk == 999
        reservation.refresh_from_db()
        assert reservation.status == ReservationHistory.Status.COMPLETED
