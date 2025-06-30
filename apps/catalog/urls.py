from django.urls import path

from apps.catalog.views import BookAndCopyCreateView, CopyConfirmView

app_name = "catalog"

urlpatterns = [
    path("new/", BookAndCopyCreateView.as_view(), name="new"),
    path("copy/confirm/<int:pk>/", CopyConfirmView.as_view(), name="copy_confirm"),
]
