from django.urls import path

from apps.library.views import SearchBooksView

urlpatterns = [
    path("", SearchBooksView.as_view(), name="book_search"),
]
