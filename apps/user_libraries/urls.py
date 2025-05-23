from django.urls import path

from .views import UserLoansListView

urlpatterns = [
    path("", UserLoansListView.as_view(), name="user_loans_list"),
]
