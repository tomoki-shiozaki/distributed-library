from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView

from apps.catalog.models import Book


# Create your views here.
class BookCreateView(CreateView):
    template_name = "catalog/book_form.html"
    model = Book
    fields = (
        "isbn",
        "title",
        "author",
        "publisher",
        "published_date",
        "image_url",
        "edition",
    )
