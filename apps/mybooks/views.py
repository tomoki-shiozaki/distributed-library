from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class MybooksView(TemplateView):
    template_name = "mybooks/mybooks_list.html"
