from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import View

LIBRARIAN = "librarian"


# Create your views here.
class HomePageView(View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            message = "ログインしてください"
        elif user.role == LIBRARIAN:
            message = "管理機能リンク"
        else:
            message = "一般ユーザー向けの案内"

        return render(request, "home.html", {"message": message})
