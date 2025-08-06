from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView

from apps.catalog.models import Book, Copy
from apps.core.mixins import IsGeneralMixin
from apps.library.forms import BookSearchForm, LoanForm, ReservationForm
from apps.library.models import LoanHistory, ReservationHistory
from apps.library.services import LoanService


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
    form_class = LoanForm
    template_name = "library/loan_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.copy = get_object_or_404(Copy, pk=kwargs["copy_pk"])
        self.today = timezone.now().date()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["today"] = self.today
        kwargs["initial"] = kwargs.get("initial", {})
        kwargs["initial"]["loan_date"] = self.today
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        loan_date = self.today
        due_date = form.cleaned_data["due_date"]

        if not LoanHistory.can_borrow_more(user):
            form.add_error(None, "貸出可能な上限に達しています。")
            return self.form_invalid(form)

        try:
            LoanService.loan_copy(user, self.copy, loan_date, due_date)
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)

        formatted_due_date = due_date.strftime("%Y年%m月%d日")

        messages.success(
            self.request,
            f"「{self.copy.book.title}」の貸出処理が完了しました。返却期限は {formatted_due_date} です。",
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("library:book_detail", kwargs={"pk": self.copy.book.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["book"] = self.copy.book

        context["loan_periods"] = LoanHistory.objects.filter(
            copy=self.copy,
            status=LoanHistory.Status.ON_LOAN,
        ).values("loan_date", "due_date")

        context["reservation_periods"] = ReservationHistory.objects.filter(
            copy=self.copy,
            status=ReservationHistory.Status.RESERVED,
        ).values("start_date", "end_date")

        return context


class ReservationCreateView(LoginRequiredMixin, IsGeneralMixin, CreateView):
    model = ReservationHistory
    form_class = ReservationForm
    template_name = "library/reservation_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.copy = get_object_or_404(Copy, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        user = self.request.user

        if not ReservationHistory.can_make_reservation(user):
            form.add_error(None, "予約可能な上限に達しています。")
            return self.form_invalid(form)

        try:
            ReservationHistory.reserve_copy(
                user=user,
                copy=self.copy,
                start_date=start_date,
                end_date=end_date,
            )
        except ValidationError as e:
            form.add_error(None, e.message)
            return self.form_invalid(form)

        formatted_start_date = start_date.strftime("%Y年%m月%d日")
        formatted_end_date = end_date.strftime("%Y年%m月%d日")

        messages.success(
            self.request,
            f"「{self.copy.book.title}」の予約処理が完了しました。予約期間は {formatted_start_date} ~ {formatted_end_date}です。",
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("library:book_detail", kwargs={"pk": self.copy.book.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["book"] = self.copy.book

        context["loan_periods"] = LoanHistory.objects.filter(
            copy=self.copy,
            status=LoanHistory.Status.ON_LOAN,
        ).values("loan_date", "due_date")

        context["reservation_periods"] = ReservationHistory.objects.filter(
            copy=self.copy,
            status=ReservationHistory.Status.RESERVED,
        ).values("start_date", "end_date")

        return context
