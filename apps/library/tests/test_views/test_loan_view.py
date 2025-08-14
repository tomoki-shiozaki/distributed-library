import datetime
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Book, Copy, StorageLocation
from apps.library.services.loan_service import LoanService

User = get_user_model()
LIBRARIAN = User.UserRole.LIBRARIAN
GENERAL = User.UserRole.GENERAL


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
def due(today):
    return today + timedelta(days=7)


@pytest.fixture
def loan_url(copy):
    return reverse("library:loan_create", kwargs={"copy_pk": copy.pk})


@pytest.mark.django_db
class TestLoanCreateView:

    def test_redirect_if_not_logged_in(self, client, loan_url):
        response = client.get(loan_url)
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")

    def test_librarian_user_cannot_access(self, client, loan_url, librarian):
        client.force_login(librarian)
        response = client.get(loan_url)
        assert response.status_code == 403

    def test_general_can_access(self, client, loan_url, general):
        client.force_login(general)
        response = client.get(loan_url)
        assert response.status_code == 200

    def test_get_form_initial(self, client, general, loan_url, today):
        client.force_login(general)
        response = client.get(loan_url)

        assert response.status_code == 200
        form = response.context["form"]
        # フォームの初期値に今日の日付が入っている
        assert form.initial["loan_date"] == today

    def test_successful_loan(self, client, general, loan_url, monkeypatch, today, due):
        """
        貸出フォームに正しいデータをPOSTしたときに、処理が成功して
        リダイレクトされ、成功メッセージが表示されることを確認する。

        - loan_copy() はモックされているため、実処理は行われない。
        - フォームのバリデーション（loan_date, due_date）は通る状態を前提とする。
        - 異常系（バリデーションエラー・貸出上限超え等）は別テストで確認する。
        """
        client.force_login(general)

        monkeypatch.setattr(LoanService, "can_borrow_more", lambda user: True)

        def mock_loan_copy(user, copy, loan_date, due_date):
            return

        monkeypatch.setattr(LoanService, "loan_copy", mock_loan_copy)

        response = client.post(
            loan_url,
            data={
                "loan_date": today,
                "due_date": due,
            },
        )

        assert response.status_code == 302

        messages = list(get_messages(response.wsgi_request))
        assert any("貸出処理が完了しました" in m.message for m in messages)

    def test_cannot_borrow_more(self, client, general, loan_url, monkeypatch):
        client.force_login(general)

        monkeypatch.setattr(LoanService, "can_borrow_more", lambda user: False)

        response = client.post(loan_url, data={"due_date": "2024-12-31"})

        # ステータスコードは200（フォームエラーで再表示）
        assert response.status_code == 200

        form = response.context["form"]
        # non_field_errorsにエラーメッセージがあるか
        errors = form.non_field_errors()
        assert "貸出可能な上限に達しています" in errors

    def test_loan_copy_raises_validation_error(
        self, client, general, loan_url, monkeypatch
    ):
        client.force_login(general)

        monkeypatch.setattr(LoanService, "can_borrow_more", lambda user: True)

        def mock_loan_copy(user, copy, loan_date, due_date):

            raise ValidationError("貸出処理エラー")

        monkeypatch.setattr(LoanService, "loan_copy", mock_loan_copy)

        response = client.post(loan_url, data={"due_date": "2024-12-31"})

        assert response.status_code == 200
        form = response.context["form"]
        errors = form.non_field_errors()
        assert "貸出処理エラー" in errors
