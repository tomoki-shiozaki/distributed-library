from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.views.generic.edit import FormView
from django.db import transaction
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from apps.catalog.forms import ISBNCheckForm
from apps.catalog.forms import BookForm, CopyForm
from apps.catalog.models import Book, Copy


# Create your views here.
class IsLibrarianMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_librarian


class ISBNCheckView(LoginRequiredMixin, IsLibrarianMixin, FormView):
    template_name = "catalog/isbn_check.html"
    form_class = ISBNCheckForm

    def form_valid(self, form):
        isbn = form.cleaned_data["isbn"]
        try:
            book = Book.objects.get(isbn=isbn)
            return redirect("catalog:copy_new", book_id=book.id)
        except Book.DoesNotExist:
            return redirect("book_create_from_isbn", isbn=isbn)


class CopyCreateView(LoginRequiredMixin, IsLibrarianMixin, CreateView):
    model = Copy
    fields = ["location", "status"]
    template_name = "catalog/copy_form.html"
    success_url = reverse_lazy("home")


class BookAndCopyCreateView(LoginRequiredMixin, IsLibrarianMixin, View):
    template_name = "catalog/book_form.html"

    def get(self, request):
        book_form = BookForm()
        copy_form = CopyForm()
        return render(
            request,
            self.template_name,
            {
                "book_form": book_form,
                "copy_form": copy_form,
            },
        )

    def post(self, request):
        book_form = BookForm(request.POST)
        copy_form = CopyForm(request.POST)

        book_form_valid = book_form.is_valid()
        copy_form_valid = copy_form.is_valid()

        if book_form_valid and copy_form_valid:
            isbn = book_form.cleaned_data["isbn"]

            # Bookを取得または作成
            book, created = Book.objects.get_or_create(
                isbn=isbn, defaults=book_form.cleaned_data
            )

            with transaction.atomic():
                copy = copy_form.save(commit=False)
                copy.book = book
                copy.save()

            return redirect("catalog:copy_confirm", copy.pk)

        # エラーがある場合は再表示
        return render(
            request,
            self.template_name,
            {
                "book_form": book_form,
                "copy_form": copy_form,
            },
        )


class CopyConfirmView(LoginRequiredMixin, IsLibrarianMixin, TemplateView):
    template_name = "catalog/copy_confirm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        copy = get_object_or_404(Copy, pk=pk)
        book = copy.book
        context["copy"] = copy
        context["book"] = book

        return context
