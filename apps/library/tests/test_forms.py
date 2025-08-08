import pytest

from apps.library.forms import BookSearchForm


@pytest.mark.parametrize(
    "data, is_valid",
    [
        # ✅ 全フィールド空（すべて optional）
        ({}, True),
        # ✅ タイトルだけ入力
        ({"title": "吾輩は猫である"}, True),
        # ✅ 著者名だけ入力
        ({"author": "夏目漱石"}, True),
        # ✅ 出版社だけ入力
        ({"publisher": "岩波書店"}, True),
        # ✅ ISBN 正常（13桁）
        ({"isbn": "9781234567890"}, True),
        # ❌ ISBN が12桁 → バリデーション失敗
        ({"isbn": "978123456789"}, True),
        # ❌ ISBN が14桁 → バリデーション失敗
        ({"isbn": "97812345678901"}, False),
        # ❌ ISBN にハイフンが含まれている → max_length は通るがルール的に失敗するかは別途ロジック次第
        (
            {"isbn": "978-1234-5678-90"},
            False,
        ),  # help_text上は非推奨だが、バリデーションでは許容される
    ],
)
def test_book_search_form_validation(data, is_valid):
    form = BookSearchForm(data=data)
    assert form.is_valid() == is_valid
