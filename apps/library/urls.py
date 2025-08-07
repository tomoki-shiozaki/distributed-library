from django.urls import path

from apps.library.views import (
    BookDetailView,
    BookSearchView,
    LoanCreateView,
    ReservationCreateView,
)

app_name = "library"

urlpatterns = [
    path("books/search/", BookSearchView.as_view(), name="book_search"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book_detail"),
    path(
        "copies/<int:copy_pk>/loan/new/", LoanCreateView.as_view(), name="loan_create"
    ),
    path(
        "copies/<int:pk>/reservation/new/",
        ReservationCreateView.as_view(),
        name="reservation_create",
    ),
]
