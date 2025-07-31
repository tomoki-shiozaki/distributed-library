from django.urls import path

from apps.user_libraries.views import CopyReturnView, MyLibraryView

app_name = "user_libraries"

urlpatterns = [
    path("", MyLibraryView.as_view(), name="my_library"),
    path("return/<int:loan_id>/", CopyReturnView.as_view(), name="copy_return"),
]
