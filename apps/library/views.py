from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.core.mixins import IsGeneralMixin
from apps.catalog.models import Book, Copy
from apps.library.forms import BookSearchForm


# Create your views here.
class BookSearchView(LoginRequiredMixin, IsGeneralMixin, ListView):
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
            isbn = self.form.cleaned_data.get("isbn")

            if title:
                queryset = queryset.filter(title__icontains=title)
            if author:
                queryset = queryset.filter(author__icontains=author)
            if publisher:
                queryset = queryset.filter(publisher__icontains=publisher)
            if isbn:
                queryset = queryset.filter(isbn__icontains=isbn)

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


class BookDetailView(LoginRequiredMixin, IsGeneralMixin, DetailView):
    model = Book
    template_name = "library/book_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 廃棄済みを除外し、貸出可能→貸出中の順にソート
        context["copies"] = (
            Copy.objects.filter(book=self.object)
            .exclude(status=Copy.Status.DISCARDED)
            .annotate(
                status_order=Case(
                    When(status=Copy.Status.AVAILABLE, then=Value(1)),
                    When(status=Copy.Status.LOANED, then=Value(2)),
                    output_field=IntegerField(),
                )
            )
            .order_by("status_order")
        )
        return context
