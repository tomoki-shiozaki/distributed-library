from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.core.mixins import (
    IsLibrarianMixin,
)

User = get_user_model()


class DummyLibrarianView(IsLibrarianMixin):
    def __init__(self, user):
        self.request = type("Request", (), {"user": user})()


class IsLibrarianMixinUnitTest(TestCase):
    def setUp(self):
        self.librarian = User.objects.create_user(
            username="lib", password="pass", role=User.UserRole.LIBRARIAN
        )
        self.general = User.objects.create_user(
            username="gen", password="pass", role=User.UserRole.GENERAL
        )

    def test_librarian_passes_test_func(self):
        view = DummyLibrarianView(self.librarian)
        assert view.test_func() is True

    def test_general_user_fails_test_func(self):
        view = DummyLibrarianView(self.general)
        assert view.test_func() is False
