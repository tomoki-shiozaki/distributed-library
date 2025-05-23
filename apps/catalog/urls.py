from django.urls import path

from apps.catalog.views import BookCreateView

app_name = "catalog"

urlpatterns = [
    path("books/create/", BookCreateView.as_view(), name="create_book"),
]
