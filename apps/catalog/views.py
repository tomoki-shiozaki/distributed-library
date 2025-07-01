import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.views.generic.edit import FormView
from django.db import transaction
from django.urls import reverse, reverse_lazy
from django.contrib import messages
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
            return redirect("catalog:book_create_from_isbn", isbn=isbn)


class BookCreateView(LoginRequiredMixin, IsLibrarianMixin, CreateView):
    model = Book
    fields = [
        "isbn",
        "title",
        "author",
        "publisher",
        "published_date",
        "image_url",
        "edition",
    ]
    template_name = "catalog/book_form.html"

    def get_initial(self):
        initial = super().get_initial()
        isbn = self.kwargs.get("isbn")
        if isbn:
            # Google Books APIから情報取得
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data["totalItems"] > 0:
                    volume_info = data["items"][0]["volumeInfo"]
                    # 初期値としてフォームに埋め込む
                    initial.update(
                        {
                            "isbn": isbn,
                            "title": volume_info.get("title", ""),
                            "author": ", ".join(volume_info.get("authors", [])),
                            "publisher": volume_info.get("publisher", ""),
                            "published_date": volume_info.get("publishedDate", ""),
                            "image_url": volume_info.get("imageLinks", {}).get(
                                "thumbnail", ""
                            ),
                            "edition": volume_info.get(
                                "contentVersion", ""
                            ),  # 適切な変換が必要なら修正
                        }
                    )
                else:
                    messages.warning(
                        self.request, f"ISBN {isbn} の書籍情報は見つかりませんでした。"
                    )
            else:
                messages.error(
                    self.request, "Google Books API からの情報取得に失敗しました。"
                )
        return initial

    def get_success_url(self):
        return reverse("catalog:copy_new", kwargs={"book_id": self.object.id})


class CopyCreateView(LoginRequiredMixin, IsLibrarianMixin, CreateView):
    model = Copy
    fields = ["location", "status"]
    template_name = "catalog/copy_form.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        book_id = self.kwargs.get("book_id")
        book = get_object_or_404(Book, id=book_id)
        form.instance.book = book
        return super().form_valid(form)


class BookAndCopyCreateView(LoginRequiredMixin, IsLibrarianMixin, View):
    template_name = "catalog/book_form_old.html"

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
