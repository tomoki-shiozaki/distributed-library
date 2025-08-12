import pytest

from apps.library.forms import BookSearchForm


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
