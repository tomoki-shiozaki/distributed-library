# from django.test import RequestFactory, TestCase
# from django.contrib.auth import get_user_model

# from apps.catalog.views import IsLibrarianMixin

# User = get_user_model()


# class DummyView(IsLibrarianMixin):
#     def __init__(self, request):
#         self.request = request


# class IsLibrarianMixinTests(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()

#     def test_librarian_passes(self):
#         user = User(username="lib", is_librarian=True)
#         request = self.factory.get("/")
#         request.user = user
#         view = DummyView(request)
#         self.assertTrue(view.test_func())

#     def test_non_librarian_fails(self):
#         user = User(username="user", is_librarian=False)
#         request = self.factory.get("/")
#         request.user = user
#         view = DummyView(request)
#         self.assertFalse(view.test_func())
