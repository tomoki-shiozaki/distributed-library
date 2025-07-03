from django.test import TestCase
import datetime
from django.utils import timezone

from apps.catalog.models import Book, StorageLocation, CopyStatus, Copy


# Create your tests here.
class TestBookModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.book = Book.objects.create(
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


class TestStorageLocationModel(TestCase):

    def test_create_storage_location(self):
        location = StorageLocation.objects.create(name="第1書庫")
        self.assertEqual(location.name, "第1書庫")
        self.assertEqual(str(location), "第1書庫")
        self.assertEqual(location._meta.verbose_name, "保存場所")
        self.assertEqual(location._meta.verbose_name_plural, "保存場所マスター")


class TestCopyModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.book = Book.objects.create(
            isbn="1234567890123",
            title="hogehoge",
            author="hugahuga",
            publisher="A出版社",
            published_date=datetime.date(2025, 5, 26),
            image_url="https://example.jp/1234567890123.jpg",
            edition=1,
        )
        cls.location = StorageLocation.objects.create(name="第1書庫")

    def test_create_copy(self):
        copy = Copy.objects.create(
            book=self.book, location=self.location, status=CopyStatus.AVAILABLE
        )
        self.assertEqual(copy.book.title, "hogehoge")
        self.assertEqual(copy.location.name, "第1書庫")
        self.assertEqual(copy.status, CopyStatus.AVAILABLE)
        self.assertEqual(copy._meta.verbose_name, "蔵書")
        self.assertEqual(copy._meta.verbose_name_plural, "蔵書一覧")
        self.assertIsNotNone(copy.registered_date)
        self.assertEqual(copy.registered_date, timezone.now().date())

    def test_status_choices(self):
        valid_statuses = dict(CopyStatus.choices)
        for key in [CopyStatus.AVAILABLE, CopyStatus.LOANED, CopyStatus.DISCARDED]:
            self.assertIn(key, valid_statuses)
