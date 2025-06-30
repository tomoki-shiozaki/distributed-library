from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from apps.catalog.forms import BookForm, CopyForm
from apps.catalog.models import Book, Copy


# Create your views here.
class BookAndCopyCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "catalog/book_form.html"

    def test_func(self):
        return self.request.user.is_librarian

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

        isbn = request.POST.get("isbn")
        try:
            book = Book.objects.get(isbn=isbn)
            created = False
            book_form_is_valid = True
        except Book.DoesNotExist:
            book = None
            created = True
            book_form_is_valid = book_form.is_valid()

        copy_form_is_valid = copy_form.is_valid()

        if book_form_is_valid and copy_form_is_valid:
            with transaction.atomic():
                if created:
                    book = book_form.save()
                copy = copy_form.save(commit=False)
                copy.book = book
                copy.save()
            return redirect("catalog:copy_confirm", copy.pk)

        # エラーがあれば再表示
        return render(
            request,
            self.template_name,
            {
                "book_form": book_form,
                "copy_form": copy_form,
            },
        )


class CopyConfirmView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "catalog/copy_confirm.html"

    def test_func(self):
        return self.request.user.is_librarian

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        copy = get_object_or_404(Copy, pk=pk)
        book = copy.book
        context["copy"] = copy
        context["book"] = book

        return context
