from django.contrib.auth.mixins import UserPassesTestMixin


class IsLibrarianMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_librarian
