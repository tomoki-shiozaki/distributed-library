import datetime
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Book, Copy, StorageLocation
from apps.library.services.reservation_service import ReservationService

User = get_user_model()
GENERAL = User.UserRole.GENERAL
LIBRARIAN = User.UserRole.LIBRARIAN


@pytest.fixture
def general(db):
    return User.objects.create_user(username="gen", password="pass", role=GENERAL)


@pytest.fixture
def librarian(db):
    return User.objects.create_user(username="lib", password="pass", role=LIBRARIAN)


@pytest.fixture
def location(db):
    return StorageLocation.objects.create(name="第1書庫")


@pytest.fixture
def copy(location):
    book = Book.objects.create(
        title="テスト本",
        author="著者名",
        publisher="出版社名",
        isbn="1234567890123",
        published_date=datetime.date(2024, 1, 1),
    )
    return Copy.objects.create(
        book=book, location=location, status=Copy.Status.AVAILABLE
    )


@pytest.fixture
def today():
    return timezone.now().date()


@pytest.fixture
def start_date(today):
    return today + timedelta(days=1)


@pytest.fixture
def end_date(today):
    return today + timedelta(days=7)


@pytest.fixture
def reservation_url(copy):
    return reverse("library:reservation_create", kwargs={"pk": copy.pk})


@pytest.mark.django_db
class TestReservationCreateView:

    def test_redirect_if_not_logged_in(self, client, reservation_url):
        response = client.get(reservation_url)
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")

    def test_librarian_user_cannot_access(self, client, reservation_url, librarian):
        client.force_login(librarian)
        response = client.get(reservation_url)
        assert response.status_code == 403

    def test_general_can_access(self, client, reservation_url, general):
        client.force_login(general)
        response = client.get(reservation_url)
        assert response.status_code == 200

    def test_successful_reservation(
        self, client, general, reservation_url, monkeypatch, start_date, end_date
    ):
        """
        予約フォームに正しいデータをPOSTしたときに成功し、リダイレクトと成功メッセージが表示されることを確認。
        ReservationService.reserve_copy はモックされているため実処理は行わない。
        """
        client.force_login(general)

        monkeypatch.setattr(
            ReservationService, "can_make_reservation", lambda user: True
        )

        def mock_reserve_copy(user, copy, start_date, end_date):
            assert isinstance(start_date, datetime.date)
            assert isinstance(end_date, datetime.date)
            return

        monkeypatch.setattr(ReservationService, "reserve_copy", mock_reserve_copy)

        response = client.post(
            reservation_url,
            data={
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        assert response.status_code == 302
        messages = list(get_messages(response.wsgi_request))
        assert any("予約処理が完了しました" in m.message for m in messages)

    def test_cannot_make_more_reservations(
        self, client, general, reservation_url, monkeypatch, start_date, end_date
    ):
        client.force_login(general)

        monkeypatch.setattr(
            ReservationService, "can_make_reservation", lambda user: False
        )

        response = client.post(
            reservation_url,
            data={
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        assert response.status_code == 200
        form = response.context["form"]
        errors = form.non_field_errors()
        assert any("予約可能な上限に達しています" in e for e in errors)

    def test_reserve_copy_raises_validation_error(
        self, client, general, reservation_url, monkeypatch, start_date, end_date
    ):
        client.force_login(general)

        monkeypatch.setattr(
            ReservationService, "can_make_reservation", lambda user: True
        )

        def mock_reserve_copy(*args, **kwargs):
            raise ValidationError("予約処理エラー")

        monkeypatch.setattr(ReservationService, "reserve_copy", mock_reserve_copy)

        response = client.post(
            reservation_url,
            data={
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        assert response.status_code == 200
        form = response.context["form"]
        errors = form.non_field_errors()
        assert any("予約処理エラー" in e for e in errors)

    def test_context_data_contains_expected_keys(
        self, client, general, reservation_url, copy
    ):
        client.force_login(general)
        response = client.get(reservation_url)

        context = response.context

        assert "book" in context
        assert context["book"] == copy.book

        assert "loan_periods" in context
        assert hasattr(context["loan_periods"], "__iter__")

        assert "reservation_periods" in context
        assert hasattr(context["reservation_periods"], "__iter__")
