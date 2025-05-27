from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.db import transaction
from django.urls import reverse

from apps.catalog.forms import BookForm, CopyForm
from apps.catalog.models import Book


# Create your views here.
# class BookCreateView(CreateView):
#     template_name = "catalog/book_form.html"
#     model = Book
#     fields = (
#         "isbn",
#         "title",
#         "author",
#         "publisher",
#         "published_date",
#         "image_url",
#         "edition",
#     )

#     def form_valid(self, form):
#         # Bookの作成
#         book = form.save()

#         # Copyの作成（BookとCopyの紐付け）
#         Copy.objects.create(book=book, location=)

#         return redirect("hoge")


def create_book_and_copy(request):
    if request.method == "POST":
        book_form = BookForm(request.POST)
        copy_form = CopyForm(request.POST)

        if book_form.is_valid() and copy_form.is_valid():
            with transaction.atomic():
                # 1. 親モデルのBookを保存
                book = book_form.save()
                # 入力されたAuthor.nameで既存のレコードを探す
                # book_isbn = book_form.cleaned_data["isbn"]
                # book, created = Book.objects.get_or_create(isbn=book_isbn)

                # 2. 子モデルのCopyを保存(commit=Falseでインスタンスだけ作成)
                copy = copy_form.save(commit=False)

                # 3. Copyに親のBookをセット
                copy.book = book

                # 4. Copyを保存
                copy.save()

            return redirect(reverse("home"))

    else:
        book_form = BookForm()
        copy_form = CopyForm()

    return render(
        request,
        "catalog/book_form.html",
        {
            "book_form": book_form,
            "copy_form": copy_form,
        },
    )
