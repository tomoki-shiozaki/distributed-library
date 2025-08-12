from datetime import timedelta

import pytest
from django.utils import timezone

from apps.library.forms import BookSearchForm, LoanForm


@pytest.fixture
def today():
    return timezone.now().date()


@pytest.fixture
def valid_due_date(today):
    return today + timedelta(days=7)


@pytest.mark.parametrize(
    "data, is_valid",
    [
        ({}, True),
        ({"title": "吾輩は猫である"}, True),
        ({"author": "夏目漱石"}, True),
        ({"publisher": "岩波書店"}, True),
        ({"isbn": "9781234567890"}, True),
        ({"isbn": "978123456789"}, True),  # 12桁 → OK（max_length制限ではない）
        ({"isbn": "97812345678901"}, False),  # 14桁 → NG（max_length超え）
    ],
)
def test_book_search_form_validation(data, is_valid):
    form = BookSearchForm(data=data)
    assert form.is_valid() == is_valid


@pytest.mark.django_db
class TestLoanFormValidation:

    def test_valid_loan_date(self, today, valid_due_date):
        form = LoanForm(
            data={
                "loan_date": today,
                "due_date": valid_due_date,
            },
            today=today,
        )
        assert form.is_valid()

    def test_invalid_loan_date(self, today, valid_due_date):
        wrong_day = today - timedelta(days=1)
        form = LoanForm(
            data={
                "loan_date": wrong_day,
                "due_date": valid_due_date,
            },
            today=today,
        )
        assert not form.is_valid()
        assert "loan_date" in form.errors
        assert "貸出日は今日以外にできません。" in form.errors["loan_date"]
