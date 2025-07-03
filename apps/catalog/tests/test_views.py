import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.catalog.models import Book

User = get_user_model()
LIBRARIAN = User.UserRole.LIBRARIAN
GENERAL = User.UserRole.GENERAL


class TestISBNCheckView(TestCase):
    def setUp(self):
        self.librarian = User.objects.create_user(
            username="lib", password="pass", role=LIBRARIAN
        )
        self.general = User.objects.create_user(
            username="gen", password="pass", role=GENERAL
        )
        self.book = Book.objects.create(
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
