from django.urls import path

from apps.library.views import BookSearchView, BookDetailView

app_name = "library"

urlpatterns = [
    path("books/search/", BookSearchView.as_view(), name="book_search"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book_detail"),
]
