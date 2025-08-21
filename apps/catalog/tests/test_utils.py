from datetime import date

import pytest

from apps.catalog.models import Book
from apps.catalog.utils import parse_published_date


@pytest.mark.parametrize(
    "input_str, expected_date, expected_precision",
    [
        ("2025-08-21", date(2025, 8, 21), Book.PublishedDatePrecision.DAY),
        ("2025-08", date(2025, 8, 1), Book.PublishedDatePrecision.MONTH),
        ("2025", date(2025, 1, 1), Book.PublishedDatePrecision.YEAR),
        ("", None, Book.PublishedDatePrecision.UNKNOWN),
        (None, None, Book.PublishedDatePrecision.UNKNOWN),
        ("invalid", None, Book.PublishedDatePrecision.UNKNOWN),
        ("2025-13-01", None, Book.PublishedDatePrecision.UNKNOWN),
        ("2025-12-32", None, Book.PublishedDatePrecision.UNKNOWN),
    ],
)
def test_parse_published_date(input_str, expected_date, expected_precision):
    result_date, result_precision = parse_published_date(input_str)
    assert result_date == expected_date
    assert result_precision == expected_precision
