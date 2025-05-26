from django.test import TestCase
import datetime

from apps.catalog.models import Book


# Create your tests here.
class TestBook(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            isbn="1234567890123",
            title="hogehoge",
            author="hugahuga",
            publisher="A出版社",
            published_date=datetime.date(2025, 5, 26),
            image_url="https://example.jp/1234567890123.jpg",
            edition=1,
        )

    def test_create_book(self):
        book = self.book
        self.assertEqual(Book.objects.all().count(), 1)
        self.assertEqual(book.isbn, "1234567890123")
        self.assertEqual(book.title, "hogehoge")
        self.assertEqual(book.author, "hugahuga")
        self.assertEqual(book.publisher, "A出版社")
        self.assertEqual(book.published_date, datetime.date(2025, 5, 26))
        self.assertEqual(book.image_url, "https://example.jp/1234567890123.jpg")
        self.assertEqual(book.edition, 1)

    def test_str_representation(self):
        book = self.book
        self.assertEqual(str(book), "hogehoge（第1版）")
