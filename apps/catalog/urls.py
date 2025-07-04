from django.urls import path

from apps.catalog.views import (
    ISBNCheckView,
    BookCreateView,
    CopyCreateView,
    CopyConfirmView,
)

app_name = "catalog"

urlpatterns = [
    path("books/isbn-check/", ISBNCheckView.as_view(), name="isbn_check"),
    path(
        "books/new/<str:isbn>/", BookCreateView.as_view(), name="book_create_from_isbn"
    ),
    path("copies/new/<int:book_id>/", CopyCreateView.as_view(), name="copy_new"),
    path("copies/<int:pk>/confirm/", CopyConfirmView.as_view(), name="copy_confirm"),
]
