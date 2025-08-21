import datetime
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
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


@pytest.mark.django_db
class TestLoanReturnView:

    def test_successful_return(
        self, client, general, loan_history, my_library_url, return_url
    ):
        """
        ユーザーが貸出中の本を返却した場合、正常に処理されること。
        """
        client.force_login(general)
        response = client.post(return_url)

        loan_history.refresh_from_db()
        assert loan_history.status == LoanHistory.Status.RETURNED
        assert response.status_code == 302
        assert response.url == my_library_url

        messages = list(get_messages(response.wsgi_request))
        assert any("返却が完了しました。" in str(m) for m in messages)

    def test_already_returned(self, client, general, loan_history, return_url):
        """
        すでに返却済みの本に対してPOSTした場合、警告メッセージが表示され、処理されないこと。
        """
        loan_history.status = LoanHistory.Status.RETURNED
        loan_history.save()

        client.force_login(general)
        response = client.post(return_url)

        loan_history.refresh_from_db()
        assert loan_history.status == LoanHistory.Status.RETURNED  # 変化なし
        assert response.status_code == 302
        assert response.url == reverse("user_libraries:my_library")

        messages = list(get_messages(response.wsgi_request))
        assert any("この本はすでに返却されています。" in str(m) for m in messages)

    def test_return_invalid_user_access(
        self, client, general, loan_history, return_url, django_user_model
    ):
        """
        他人の貸出履歴に対して返却を試みると404になること。
        """
        another_user = django_user_model.objects.create_user(
            username="other", password="pass"
        )
        loan_history.user = another_user
        loan_history.save()

        client.force_login(general)
        response = client.post(return_url)
        assert response.status_code == 404
