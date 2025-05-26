from django.urls import path

from .views import UserLoanListView

app_name = "user_libraries"

urlpatterns = [
    path("", UserLoanListView.as_view(), name="user_loan_list"),
]
