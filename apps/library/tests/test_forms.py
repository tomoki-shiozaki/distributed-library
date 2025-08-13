import datetime
from datetime import timedelta

import pytest
from django import forms
from django.utils import timezone

from apps.library.forms import BookSearchForm, LoanForm, ReservationForm


@pytest.fixture
def today():
    return timezone.now().date()


@pytest.fixture
def valid_due_date(today):
    return today + timedelta(days=7)


@pytest.fixture
def valid_reservation_data(today):
    return {
        "start_date": today + datetime.timedelta(days=1),
        "end_date": today + datetime.timedelta(days=5),
    }


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
class TestLoanForm:

    def test_form_has_required_fields(self, today):
        form = LoanForm(today=today)
        assert "loan_date" in form.fields
        assert "due_date" in form.fields

    def test_loan_date_is_hidden(self, today):
        form = LoanForm(today=today)
        assert isinstance(form.fields["loan_date"].widget, forms.HiddenInput)

    def test_due_date_widget_is_date_input(self, today):
        form = LoanForm(today=today)
        assert form.fields["due_date"].widget.input_type == "date"

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


@pytest.mark.django_db
class TestReservationForm:
    def test_form_has_required_fields(self):
        form = ReservationForm()
        assert "start_date" in form.fields
        assert "end_date" in form.fields

    def test_widgets_are_date_inputs(self):
        form = ReservationForm()
        assert form.fields["start_date"].widget.input_type == "date"
        assert form.fields["end_date"].widget.input_type == "date"

    def test_help_texts_are_correct(self):
        form = ReservationForm()
        assert (
            form.fields["start_date"].help_text
            == "予約は本日以降の日付を指定してください。"
        )
        assert form.fields["end_date"].help_text == "予約期間は最長14日間です。"
