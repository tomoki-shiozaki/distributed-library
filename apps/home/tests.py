from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from apps.accounts.models import CustomUser

GENERAL = CustomUser.GENERAL
LIBRARIAN = CustomUser.LIBRARIAN


# Create your tests here.
class HomePageTests(TestCase):

    def test_home_page_status_code(self):
        response = self.client.get("/")
        self.assertEqual(
            response.status_code, 200
        )  # ステータスコードが200であることを確認

    def test_view_url_by_name(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")


class TopPageViewTests(TestCase):
    def setUp(self):
        self.url = reverse("home")

    def test_top_page_for_anonymous_user(self):
        response = self.client.get(self.url)
        self.assertContains(response, "ログインしてください")
        self.assertContains(response, f'href="{reverse("login")}"')
        self.assertContains(response, f'href="{reverse("signup")}"')

    def test_top_page_for_general_user(self):
        user = get_user_model().objects.create_user(
            username="user",
            email="user@example.com",
            password="testpass",
            role=GENERAL,
        )
        self.client.login(username="user", password="testpass")
        response = self.client.get(self.url)
        self.assertContains(response, "一般ユーザー向けの案内")
        self.assertContains(response, f'href="{reverse("book_search")}"')
        self.assertContains(response, f'href="{reverse("user_loans_list")}"')

    def test_top_page_for_librarian_user(self):
        librarian = get_user_model().objects.create_user(
            username="librarian",
            email="lib@example.com",
            password="testpass",
            role=LIBRARIAN,
        )
        self.client.login(username="librarian", password="testpass")
        response = self.client.get(self.url)
        self.assertContains(response, "司書向けの案内")
        self.assertContains(response, f'href="{reverse("catalog:create_book")}"')
