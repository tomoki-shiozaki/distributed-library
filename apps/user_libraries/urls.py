from django.urls import path

from apps.user_libraries.views import MyLibraryView

app_name = "user_libraries"

urlpatterns = [
    path("", MyLibraryView.as_view(), name="my_library"),
]
