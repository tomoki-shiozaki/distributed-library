from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from apps.core.mixins import IsGeneralMixin
from apps.catalog.models import Book, Copy
from apps.library.forms import BookSearchForm
from apps.library.models import LoanHistory, ReservationHistory
from apps.library.utils import book_has_available_copy


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
            available_count=Count(
                "copies", filter=Q(copies__status=Copy.Status.AVAILABLE)
            ),
            loaned_count=Count("copies", filter=Q(copies__status=Copy.Status.LOANED)),
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
        context["COPY_STATUS"] = Copy.Status
        return context


class LoanCreateView(LoginRequiredMixin, IsGeneralMixin, CreateView):
    model = LoanHistory
    fields = [
        "loan_date",
        "due_date",
        "return_date",
    ]
    template_name = "library/loan_form.html"


class ReservationCreateView(LoginRequiredMixin, IsGeneralMixin, CreateView):
    model = ReservationHistory
    fields = ["start_date", "end_date"]
    template_name = "library/reservation_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(Book, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.book = self.book

        start = form.cleaned_data["start_date"]
        end = form.cleaned_data["end_date"]

        if not book_has_available_copy(self.book, start, end):
            form.add_error(
                None,
                "指定された期間では予約できる蔵書がありません。別の期間をお試しください。",
            )
            return self.form_invalid(form)

        messages.success(self.request, "予約が完了しました。")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("library:book_detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["book"] = self.book
        return context
