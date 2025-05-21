from django.urls import path

from .views import MybooksView

urlpatterns = [
    path("", MybooksView.as_view(), name="mybooks"),
]
