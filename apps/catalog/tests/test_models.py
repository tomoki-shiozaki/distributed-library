import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.catalog.models import Book, Copy, StorageLocation


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

    def test_clean_raises_error_if_date_is_none_but_precision_is_not_unknown(self):
        book = Book(
            isbn="9876543210123",
            title="Invalid Book",
            author="Test Author",
            published_date=None,
            published_date_precision=Book.PublishedDatePrecision.DAY,
        )
        with self.assertRaises(ValidationError) as context:
            book.clean()
        self.assertIn(
            "出版日が未入力の場合、精度は「不明」に設定してください。",
            str(context.exception),
        )

    def test_clean_raises_error_if_date_is_set_but_precision_is_unknown(self):
        book = Book(
            isbn="9876543210124",
            title="Invalid Book 2",
            author="Test Author",
            published_date=datetime.date(2025, 1, 1),
            published_date_precision=Book.PublishedDatePrecision.UNKNOWN,
        )
        with self.assertRaises(ValidationError) as context:
            book.clean()
        self.assertIn(
            "出版日が入力されている場合は、精度を「不明」以外のいずれかに選択してください。",
            str(context.exception),
        )


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
            book=self.book, location=self.location, status=Copy.Status.AVAILABLE
        )
        self.assertEqual(copy.book.title, "hogehoge")
        self.assertEqual(copy.location.name, "第1書庫")
        self.assertEqual(copy.status, Copy.Status.AVAILABLE)
        self.assertEqual(copy._meta.verbose_name, "蔵書")
        self.assertEqual(copy._meta.verbose_name_plural, "蔵書")
        self.assertIsNotNone(copy.registered_date)
        self.assertEqual(copy.registered_date, datetime.date.today())

        expected_str = (
            f"{copy.book} - {copy.location.name} - {copy.get_status_display()}"
        )
        self.assertEqual(str(copy), expected_str)

    def test_status_choices(self):
        valid_statuses = dict(Copy.Status.choices)
        for key in [Copy.Status.AVAILABLE, Copy.Status.LOANED, Copy.Status.DISCARDED]:
            self.assertIn(key, valid_statuses)
