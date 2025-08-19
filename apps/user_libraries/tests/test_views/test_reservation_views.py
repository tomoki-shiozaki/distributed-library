import datetime
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.urls import reverse
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
def location(db):
    return StorageLocation.objects.create(name="第1書庫")


@pytest.fixture
def book(db):
    return Book.objects.create(
        title="テスト本",
        author="著者名",
        publisher="出版社名",
        isbn="1234567890123",
        published_date=datetime.date(2024, 1, 1),
    )


@pytest.fixture
def copy(db, book, location):
    return Copy.objects.create(
        book=book, location=location, status=Copy.Status.AVAILABLE
    )


@pytest.fixture
def today():
    return timezone.localdate()


@pytest.fixture
def due(today):
    return today + timedelta(days=7)


@pytest.fixture
def loan_history(db, general, copy, today, due):
    return LoanHistory.objects.create(
        user=general,
        copy=copy,
        loan_date=today,
        due_date=due,
        status=LoanHistory.Status.ON_LOAN,
    )


@pytest.fixture
def reservation_history(db, general, copy, today):
    return ReservationHistory.objects.create(
        user=general,
        copy=copy,
        status=ReservationHistory.Status.RESERVED,
        start_date=today,
        end_date=today + timedelta(days=1),
    )


@pytest.fixture
def my_library_url():
    return reverse("user_libraries:my_library")


@pytest.fixture
def return_url(loan_history):
    return reverse("user_libraries:loan_return", kwargs={"pk": loan_history.pk})


@pytest.fixture
def reservation_cancel_url(reservation_history):
    return reverse(
        "user_libraries:reservation_cancel", kwargs={"pk": reservation_history.pk}
    )


@pytest.mark.django_db
class TestReservationCancelView:

    def test_successful_cancel(
        self,
        client,
        general,
        reservation_history,
        my_library_url,
        reservation_cancel_url,
    ):
        client.force_login(general)

        response = client.post(reservation_cancel_url)

        reservation_history.refresh_from_db()

        assert response.status_code == 302
        assert response.url == my_library_url

        messages = list(get_messages(response.wsgi_request))
        assert any("予約のキャンセルが完了しました。" in str(m) for m in messages)

    def test_cancel_validation_error(
        self, client, general, my_library_url, reservation_cancel_url
    ):
        client.force_login(general)

        with patch(
            "apps.library.models.ReservationHistory.cancel",
            side_effect=ValidationError("キャンセルできません"),
        ):
            response = client.post(reservation_cancel_url)

        assert response.status_code == 302
        assert response.url == my_library_url

        messages = list(get_messages(response.wsgi_request))
        assert any("キャンセルできません" in str(m) for m in messages)

    def test_cancel_other_users_reservation_returns_404(
        self,
        client,
        general,
        reservation_history,
        django_user_model,
        reservation_cancel_url,
    ):
        another_user = django_user_model.objects.create_user(
            username="other", password="pass"
        )
        reservation_history.user = another_user
        reservation_history.save()

        client.force_login(general)

        response = client.post(reservation_cancel_url)
        assert response.status_code == 404
