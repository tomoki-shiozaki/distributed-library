from django.shortcuts import render
from django.views.generic import TemplateView, ListView

from apps.catalog.models import Book
from apps.library.forms import BookSearchForm


# Create your views here.
class BookSearchView(ListView):
    model = Book
    template_name = "library/book_search.html"
    context_object_name = "books"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.form = BookSearchForm(self.request.GET)

        # 初期表示（クエリなし）は空クエリセットを返す
        if not self.request.GET:
            return queryset.none()

        if self.form.is_valid():
            title = self.form.cleaned_data.get("title")
            author = self.form.cleaned_data.get("author")
            publisher = self.form.cleaned_data.get("publisher")
            if title:
                queryset = queryset.filter(title__icontains=title)
            if author:
                queryset = queryset.filter(author__icontains=author)
            if publisher:
                queryset = queryset.filter(publisher__icontains=publisher)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context
