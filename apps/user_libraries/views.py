from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class UserLoanListView(TemplateView):
    template_name = "user_libraries/user_loan_list.html"
