from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class SearchBooksView(TemplateView):
    template_name = "library/search_books.html"
