from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.core.mixins import (
    IsLibrarianMixin,
)

User = get_user_model()


class DummyRequest:
    def __init__(self, user):
        self.user = user


class DummyLibrarianView(IsLibrarianMixin):
    def __init__(self, user):
        self.request = DummyRequest(user)


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
        self.assertTrue(view.test_func())

    def test_general_user_fails_test_func(self):
        view = DummyLibrarianView(self.general)
        self.assertFalse(view.test_func())
