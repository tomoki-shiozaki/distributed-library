import datetime

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.catalog.models import Book, Copy, StorageLocation

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
def books_with_copies(db, location):
    book1 = Book.objects.create(
        title="Python入門",
        author="田中",
        publisher="出版社A",
        isbn="1111111111111",
        published_date=datetime.date(2024, 1, 1),
    )
    book2 = Book.objects.create(
        title="Django実践",
        author="佐藤",
        publisher="出版社B",
        isbn="2222222222222",
        published_date=datetime.date(2024, 1, 1),
    )
    Copy.objects.create(book=book1, location=location, status=Copy.Status.AVAILABLE)
    Copy.objects.create(book=book1, location=location, status=Copy.Status.LOANED)
    return book1, book2


@pytest.fixture
def book_search_url():
    return reverse("library:book_search")


@pytest.mark.django_db
class TestBookSearchView:

    def test_initial_no_query_returns_empty_queryset(
        self, client, general, book_search_url
    ):
        client.force_login(general)
        response = client.get(book_search_url)  # クエリなしGET

        assert response.status_code == 200
        books = response.context["books"]
        assert books.count() == 0

    def test_filter_by_title(self, client, general, books_with_copies, book_search_url):
        client.force_login(general)
        response = client.get(book_search_url, {"title": "Python"})

        assert response.status_code == 200
        books = response.context["books"]
        book1, book2 = books_with_copies

        assert book1 in books
        assert book2 not in books

        # annotateの検証
        book = next((b for b in books if b.pk == book1.pk), None)
        assert book is not None
        assert book.available_count == 1
        assert book.loaned_count == 1

    def test_filter_by_author(
        self, client, general, books_with_copies, book_search_url
    ):
        client.force_login(general)
        response = client.get(book_search_url, {"author": "田中"})

        assert response.status_code == 200
        books = response.context["books"]
        book1, book2 = books_with_copies

        assert book1 in books
        assert book2 not in books

    def test_filter_by_publisher(
        self, client, general, books_with_copies, book_search_url
    ):
        client.force_login(general)
        response = client.get(book_search_url, {"publisher": "出版社A"})

        assert response.status_code == 200
        books = response.context["books"]
        book1, book2 = books_with_copies

        assert book1 in books
        assert book2 not in books

    def test_filter_by_isbn(self, client, general, books_with_copies, book_search_url):
        client.force_login(general)
        response = client.get(book_search_url, {"isbn": "1111111111111"})

        assert response.status_code == 200
        books = response.context["books"]
        book1, book2 = books_with_copies

        assert book1 in books
        assert book2 not in books

    def test_get_context_data_contains_form(self, client, general, book_search_url):
        client.force_login(general)
        response = client.get(book_search_url, {"title": "Python"})

        assert response.status_code == 200
        form = response.context.get("form")
        assert form is not None
        assert form.is_bound  # フォームはバインドされている

    def test_invalid_form_returns_unfiltered_queryset_with_annotation(
        self, client, general, books_with_copies, book_search_url
    ):
        client.force_login(general)
        response = client.get(book_search_url, {"isbn": " "})  # 空白だけの不正値

        assert response.status_code == 200
        books = response.context["books"]
        book1, book2 = books_with_copies

        # フィルターがかからず両方表示される
        assert book1 in books
        assert book2 in books


@pytest.fixture
def book_with_copies(location):
    book = Book.objects.create(
        title="テスト本",
        author="著者名",
        publisher="出版社名",
        isbn="1234567890123",
        published_date=datetime.date(2024, 1, 1),
    )
    Copy.objects.create(book=book, location=location, status=Copy.Status.AVAILABLE)
    Copy.objects.create(book=book, location=location, status=Copy.Status.LOANED)
    Copy.objects.create(book=book, location=location, status=Copy.Status.DISCARDED)
    return book


@pytest.fixture
def book_detail_url(book_with_copies):
    return reverse("library:book_detail", args=[book_with_copies.pk])


@pytest.mark.django_db
class TestBookDetailView:

    def test_book_detail_view_context(
        self, client, book_detail_url, general, book_with_copies
    ):
        client.force_login(general)
        response = client.get(book_detail_url)

        assert response.status_code == 200

        # 本の詳細
        assert response.context["object"] == book_with_copies

        # COPY_STATUS が含まれている
        assert "COPY_STATUS" in response.context

        # copies の内容を検証
        copies = response.context["copies"]
        statuses = [copy.status for copy in copies]

        # 廃棄済みを除いたコピーの件数（book_with_copiesのコピーでDISCARDED以外の件数）
        expected_count = (
            Copy.objects.filter(book=book_with_copies)
            .exclude(status=Copy.Status.DISCARDED)
            .count()
        )
        assert len(copies) == expected_count, "copiesの件数が期待値と異なります"

        # 廃棄されたコピーは含まれていない
        assert Copy.Status.DISCARDED not in statuses

        # 順番が AVAILABLE → LOANED になっているか
        assert statuses == sorted(
            statuses, key=lambda s: {Copy.Status.AVAILABLE: 1, Copy.Status.LOANED: 2}[s]
        )
