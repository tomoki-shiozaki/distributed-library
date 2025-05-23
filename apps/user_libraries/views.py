from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class UserLoansListView(TemplateView):
    template_name = "user_libraries/user_loans_list.html"
