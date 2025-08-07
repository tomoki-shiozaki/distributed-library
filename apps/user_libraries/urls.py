from django.urls import path

from apps.user_libraries.views import (
    LoanReturnView,
    MyLibraryView,
    ReservationCancelView,
    ReservationLoanView,
)

app_name = "user_libraries"

urlpatterns = [
    path("", MyLibraryView.as_view(), name="my_library"),
    path("loans/<int:pk>/return/", LoanReturnView.as_view(), name="loan_return"),
    path(
        "reservations/<int:pk>/cancel/",
        ReservationCancelView.as_view(),
        name="reservation_cancel",
    ),
    path(
        "reservations/<int:pk>/loan/",
        ReservationLoanView.as_view(),
        name="reservation_loan",
    ),
]
