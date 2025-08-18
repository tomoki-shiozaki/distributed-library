import datetime
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
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
def loan_history(general, copy, db):
    return LoanHistory.objects.create(
        user=general, copy=copy, status=LoanHistory.Status.ON_LOAN
    )


@pytest.fixture
def reservation_history(general, copy, db):
    today = timezone.localdate()
    return ReservationHistory.objects.create(
        user=general,
        copy=copy,
        status=ReservationHistory.Status.RESERVED,
        start_date=today - timezone.timedelta(days=1),
        end_date=today + timezone.timedelta(days=1),
    )


@pytest.fixture
def my_library_url():
    return reverse("user_libraries:my_library")


@pytest.mark.django_db
class TestMyLibraryView:

    def test_my_library_view(self, client, general, my_library_url):
        client.force_login(general)
        response = client.get(my_library_url)
        assert response.status_code == 200
        assert "user_libraries/my_library.html" in [t.name for t in response.templates]

    # def test_loan_history_in_context(
    #     self, client, general, loan_history, my_library_url
    # ):
    #     # LoanHistoryがコンテキストに含まれていることを確認
    #     client.force_login(general)
    #     response = client.get(my_library_url)

    #     context = response.context
    #     assert "loans" in context
    #     assert len(context["loans"]) == 1
    #     assert context["loans"][0] == loan_history

    # def test_reservation_history_in_context(
    #     self, client, general, reservation_history, my_library_url
    # ):
    #     # ReservationHistoryがコンテキストに含まれていることを確認
    #     client.force_login(general)
    #     response = client.get(my_library_url)

    #     context = response.context
    #     assert "reservations" in context
    #     assert len(context["reservations"]) == 1
    #     assert context["reservations"][0] == reservation_history

    #     # 'can_loan_now' が正しく設定されていることを確認
    #     assert context["reservations"][0].can_loan_now is True

    # def test_reservation_can_loan_now_false(
    #     self, client, general, reservation_history, my_library_url
    # ):
    #     # 予約の期間が終了している場合 'can_loan_now' が False であることを確認
    #     today = timezone.localdate()
    #     reservation_history.start_date = today - timezone.timedelta(days=1)
    #     reservation_history.end_date = today - timezone.timedelta(days=1)
    #     reservation_history.save()

    #     client.force_login(general)
    #     response = client.get(my_library_url)

    #     context = response.context
    #     assert context["reservations"][0].can_loan_now is False

    # def test_reservation_no_available_copy(
    #     self, client, general, reservation_history, copy, my_library_url
    # ):
    #     # コピーが貸出中の場合 'can_loan_now' が False であることを確認
    #     copy.status = Copy.Status.ON_LOAN  # コピーを貸出中に設定
    #     copy.save()

    #     client.force_login(general)
    #     response = client.get(my_library_url)

    #     context = response.context
    #     assert context["reservations"][0].can_loan_now is False

    # def test_no_loans_or_reservations(self, client, general, my_library_url):
    #     # ユーザーに貸出履歴や予約履歴がない場合
    #     client.force_login(general)
    #     response = client.get(my_library_url)

    #     context = response.context
    #     assert len(context.get("loans", [])) == 0
    #     assert len(context.get("reservations", [])) == 0
