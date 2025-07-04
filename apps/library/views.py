from django.shortcuts import render
from django.views.generic import TemplateView, ListView

from apps.catalog.models import Book
from apps.library.forms import BookSearchForm


# Create your views here.
class BookSearchView(ListView):
    model = Book
    template_name = "library/book_search.html"
    context_object_name = "books"
    paginate_by = 2

    def get_queryset(self):
        queryset = super().get_queryset()
        self.form = BookSearchForm(self.request.GET)
        if self.form.is_valid():
            q = self.form.cleaned_data.get("q")
            if q:
                queryset = queryset.filter(title__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context
