from django.urls import path

from apps.catalog.views import BookCreateView

app_name = "catalog"

urlpatterns = [
    path("new/", BookCreateView.as_view(), name="new"),
]
