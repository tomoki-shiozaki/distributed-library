from django.urls import path

from apps.library.views import BookSearchView

app_name = "library"

urlpatterns = [
    path("books/search", BookSearchView.as_view(), name="book_search"),
]
