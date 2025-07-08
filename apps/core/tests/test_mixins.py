from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.core.mixins import (
    IsLibrarianMixin,
    IsGeneralMixin,
)

User = get_user_model()


class DummyRequest:
    def __init__(self, user):
        self.user = user


class DummyLibrarianView(IsLibrarianMixin):
    def __init__(self, user):
        self.request = DummyRequest(user)


class TestIsLibrarianMixin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.librarian = User.objects.create_user(
            username="lib", password="pass", role=User.UserRole.LIBRARIAN
        )
        cls.general = User.objects.create_user(
            username="gen", password="pass", role=User.UserRole.GENERAL
        )

    def test_librarian_passes_test_func(self):
        view = DummyLibrarianView(self.librarian)
        self.assertTrue(view.test_func())

    def test_general_user_fails_test_func(self):
        view = DummyLibrarianView(self.general)
        self.assertFalse(view.test_func())


class DummyGeneralView(IsGeneralMixin):
    def __init__(self, user):
        self.request = DummyRequest(user)


class TestIsGeneralMixin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.librarian = User.objects.create_user(
            username="lib", password="pass", role=User.UserRole.LIBRARIAN
        )
        cls.general = User.objects.create_user(
            username="gen", password="pass", role=User.UserRole.GENERAL
        )

    def test_general_user_passes_test_func(self):
        view = DummyGeneralView(self.general)
        self.assertTrue(view.test_func())

    def test_librarian_fails_test_func(self):
        view = DummyGeneralView(self.librarian)
        self.assertFalse(view.test_func())
