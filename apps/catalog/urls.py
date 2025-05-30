from django.urls import path

from apps.catalog.views import create_book_and_copy, copy_confirm

app_name = "catalog"

urlpatterns = [
    path("new/", create_book_and_copy, name="new"),
    path("copy/confirm/<int:pk>/", copy_confirm, name="copy_confirm"),
]
