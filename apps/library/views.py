from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class BookSearchView(TemplateView):
    template_name = "library/book_search.html"
