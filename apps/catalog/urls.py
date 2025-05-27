from django.urls import path

from apps.catalog.views import create_book_and_copy

app_name = "catalog"

urlpatterns = [
    path("new/", create_book_and_copy, name="new"),
]
