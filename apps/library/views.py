from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Count, Q

from apps.catalog.models import Book, Copy
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

        # 各本に貸出可能なコピーの数を追加
        queryset = queryset.annotate(
            available_count=Count("copy", filter=Q(copy__status=Copy.Status.AVAILABLE)),
            loaned_count=Count("copy", filter=Q(copy__status=Copy.Status.LOANED)),
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context
