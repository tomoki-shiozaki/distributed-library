from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.db import transaction
from django.urls import reverse

from apps.catalog.forms import BookForm, CopyForm
from apps.catalog.models import Book


# Create your views here.


def create_book_and_copy(request):
    if request.method == "POST":
        book_form = BookForm(request.POST)
        copy_form = CopyForm(request.POST)

        isbn = request.POST.get("isbn")
        try:
            # 既に存在する本を取得
            book = Book.objects.get(isbn=isbn)
            created = False
            book_form_is_valid = True  # 既存ならフォーム検証スキップ
        except Book.DoesNotExist:
            book = None
            created = True
            book_form_is_valid = book_form.is_valid()

        if book_form_is_valid and copy_form.is_valid():
            with transaction.atomic():
                if created:
                    # 新規Bookを登録
                    book = book_form.save()

                # Copyを作成・保存
                copy = copy_form.save(commit=False)
                copy.book = book
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
