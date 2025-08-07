from datetime import datetime

from apps.catalog.models import Book


def parse_published_date(published_date_str: str):
    """
    Google Books APIなどから返された publishedDate を解析し、
    datetime.date 型と精度 (YEAR, MONTH, DAY, UNKNOWN) を返す。

    Args:
        published_date_str (str): "YYYY", "YYYY-MM", "YYYY-MM-DD" のいずれか

    Returns:
        tuple: (datetime.date or None, Book.PublishedDatePrecision enum)
    """
    if not published_date_str:
        return None, Book.PublishedDatePrecision.UNKNOWN

    try:
        published_date = datetime.strptime(published_date_str, "%Y-%m-%d").date()
        precision = Book.PublishedDatePrecision.DAY
    except ValueError:
        try:
            published_date = datetime.strptime(published_date_str, "%Y-%m").date()
            published_date = published_date.replace(day=1)
            precision = Book.PublishedDatePrecision.MONTH
        except ValueError:
            try:
                published_date = datetime.strptime(published_date_str, "%Y").date()
                published_date = published_date.replace(month=1, day=1)
                precision = Book.PublishedDatePrecision.YEAR
            except ValueError:
                published_date = None
                precision = Book.PublishedDatePrecision.UNKNOWN

    return published_date, precision
