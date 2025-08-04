import datetime
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Book, Copy, StorageLocation

User = get_user_model()
LIBRARIAN = User.UserRole.LIBRARIAN
GENERAL = User.UserRole.GENERAL


class TestISBNCheckView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.librarian = User.objects.create_user(
            username="lib", password="pass", role=LIBRARIAN
        )
        cls.general = User.objects.create_user(
            username="gen", password="pass", role=GENERAL
        )
        cls.book = Book.objects.create(
            isbn="1234567890123",
            title="hogehoge",
            author="hugahuga",
            publisher="A出版社",
            published_date=datetime.date(2025, 5, 26),
            image_url="https://example.jp/1234567890123.jpg",
            edition=1,
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("catalog:isbn_check"))
        self.assertRedirects(
            response, f"/accounts/login/?next={reverse('catalog:isbn_check')}"
        )

    def test_general_user_cannot_access(self):
        self.client.login(username="gen", password="pass")
        response = self.client.get(reverse("catalog:isbn_check"))
        self.assertEqual(response.status_code, 403)

    def test_librarian_can_access(self):
        self.client.login(username="lib", password="pass")
        response = self.client.get(reverse("catalog:isbn_check"))
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_copy_new_if_book_exists(self):
        self.client.login(username="lib", password="pass")
        response = self.client.post(
            reverse("catalog:isbn_check"), data={"isbn": self.book.isbn}
        )
        self.assertRedirects(
            response, reverse("catalog:copy_new", kwargs={"book_id": self.book.id})
        )

    def test_redirect_to_book_create_from_isbn_if_book_does_not_exist(self):
        self.client.login(username="lib", password="pass")
        response = self.client.post(
            reverse("catalog:isbn_check"), data={"isbn": "9999999"}
        )
        self.assertRedirects(
            response,
            reverse("catalog:book_create_from_isbn", kwargs={"isbn": "9999999"}),
        )


class TestBookCreateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.librarian = User.objects.create_user(
            username="lib", password="pass", role=LIBRARIAN
        )

    def setUp(self):
        self.client.login(username="lib", password="pass")

    @patch("apps.catalog.views.requests.get")
    def test_get_initial_with_valid_isbn(self, mock_get):
        isbn = "1234567890"
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {
            "totalItems": 1,
            "items": [
                {
                    "volumeInfo": {
                        "title": "Test Book",
                        "authors": ["Author1", "Author2"],
                        "publisher": "Pub",
                        "publishedDate": "2020-01-01",
                        "imageLinks": {"thumbnail": "http://image.jpg"},
                    }
                }
            ],
        }
        mock_get.return_value = mock_resp

        response = self.client.get(
            reverse("catalog:book_create_from_isbn", kwargs={"isbn": isbn})
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        initial = form.initial
        self.assertEqual(initial["isbn"], isbn)
        self.assertEqual(initial["title"], "Test Book")
        self.assertIn("Author1, Author2", initial["author"])
        self.assertEqual(initial["publisher"], "Pub")
        self.assertEqual(initial["published_date"], datetime.date(2020, 1, 1))
        self.assertEqual(
            initial["published_date_precision"], Book.PublishedDatePrecision.DAY
        )
        self.assertEqual(initial["image_url"], "http://image.jpg")

    @patch("apps.catalog.views.requests.get")
    def test_get_initial_with_no_items(self, mock_get):
        isbn = "0000000"
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {"totalItems": 0}
        mock_get.return_value = mock_resp

        response = self.client.get(
            reverse("catalog:book_create_from_isbn", kwargs={"isbn": isbn})
        )
        storage = list(response.context["messages"])
        self.assertTrue(any("見つかりません" in m.message for m in storage))

    @patch("apps.catalog.views.requests.get")
    def test_get_initial_with_api_error(self, mock_get):
        isbn = "error"
        mock_resp = Mock(status_code=500)
        mock_get.return_value = mock_resp

        response = self.client.get(
            reverse("catalog:book_create_from_isbn", kwargs={"isbn": isbn})
        )
        storage = list(response.context["messages"])
        self.assertTrue(any("失敗しました" in m.message for m in storage))

    def test_post_creates_book_and_redirects(self):
        isbn = "1112223334445"
        data = {
            "isbn": isbn,
            "title": "New Title",
            "author": "A B",
            "publisher": "Pub",
            "published_date": "2025-01-01",
            "published_date_precision": Book.PublishedDatePrecision.DAY,
            "image_url": "http://example.com/image.jpg",
            "edition": 2,
        }
        response = self.client.post(
            reverse("catalog:book_create_from_isbn", kwargs={"isbn": isbn}), data=data
        )
        # Book が作成され、正しいリダイレクト先へ
        book = Book.objects.get(isbn=isbn)
        self.assertRedirects(
            response, reverse("catalog:copy_new", kwargs={"book_id": book.id})
        )
        self.assertEqual(book.title, "New Title")
        self.assertEqual(book.edition, 2)


class TestCopyCreateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.librarian = User.objects.create_user(
            username="lib", password="pass", role=LIBRARIAN
        )
        cls.general = User.objects.create_user(
            username="gen", password="pass", role=GENERAL
        )
        cls.book = Book.objects.create(
            isbn="1234567890123",
            title="Test Book",
            author="Author",
            publisher="Pub",
            published_date=datetime.date(2024, 1, 1),
            edition=1,
        )
        cls.location = StorageLocation.objects.create(name="第1書庫")

    def test_redirect_if_not_logged_in(self):
        url = reverse("catalog:copy_new", kwargs={"book_id": self.book.id})
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_general_user_forbidden(self):
        self.client.login(username="gen", password="pass")
        url = reverse("catalog:copy_new", kwargs={"book_id": self.book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_librarian_can_access_and_sees_book_in_context(self):
        self.client.login(username="lib", password="pass")
        url = reverse("catalog:copy_new", kwargs={"book_id": self.book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("book", response.context)
        self.assertEqual(response.context["book"], self.book)

    def test_post_creates_copy_and_redirects(self):
        self.client.login(username="lib", password="pass")
        url = reverse("catalog:copy_new", kwargs={"book_id": self.book.id})
        data = {"location": self.location.id, "status": Copy.Status.AVAILABLE}
        response = self.client.post(url, data)

        copy = Copy.objects.get(book=self.book)
        self.assertEqual(copy.location, self.location)
        self.assertEqual(copy.status, Copy.Status.AVAILABLE)

        self.assertRedirects(
            response, reverse("catalog:copy_confirm", kwargs={"pk": copy.pk})
        )


class TestCopyConfirmView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.librarian = User.objects.create_user(
            username="lib", password="pass", role=LIBRARIAN
        )
        cls.general = User.objects.create_user(
            username="gen", password="pass", role=GENERAL
        )
        cls.book = Book.objects.create(
            isbn="1234567890123",
            title="Test Book",
            author="Author",
            publisher="Pub",
            published_date=datetime.date(2024, 1, 1),
            edition=1,
        )
        cls.location = StorageLocation.objects.create(name="第1書庫")
        cls.copy = Copy.objects.create(
            book=cls.book,
            location=cls.location,
            status=Copy.Status.AVAILABLE,
        )
        cls.url = reverse("catalog:copy_confirm", kwargs={"pk": cls.copy.pk})

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_general_user_forbidden(self):
        self.client.login(username="gen", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_librarian_can_access(self):
        self.client.login(username="lib", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_contains_copy(self):
        self.client.login(username="lib", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.context["copy"], self.copy)
