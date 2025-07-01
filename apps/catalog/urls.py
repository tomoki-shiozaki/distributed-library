from django.urls import path

from apps.catalog.views import (
    ISBNCheckView,
    BookCreateView,
    CopyCreateView,
    BookAndCopyCreateView,
    CopyConfirmView,
)

app_name = "catalog"

urlpatterns = [
    path("books/isbn-check/", ISBNCheckView.as_view(), name="isbn_check"),
    path(
        "books/new/<str:isbn>/", BookCreateView.as_view(), name="book_create_from_isbn"
    ),
    path("copies/new/<int:book_id>/", CopyCreateView.as_view(), name="copy_new"),
    path("new/", BookAndCopyCreateView.as_view(), name="new"),
    path("copy/confirm/<int:pk>/", CopyConfirmView.as_view(), name="copy_confirm"),
]
