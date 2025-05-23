from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class BookCreateView(TemplateView):
    template_name = "catalog/book_form.html"
