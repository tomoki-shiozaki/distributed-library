from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.db import transaction
from django.urls import reverse

from apps.catalog.forms import BookForm, CopyForm
from apps.catalog.models import Book, Copy


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

            return redirect("catalog:copy_confirm", copy.pk)

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


def copy_confirm(request, pk):
    copy = get_object_or_404(Copy, pk=pk)
    book = copy.book
    return render(
        request,
        "catalog/copy_confirm.html",
        {
            "book": book,
            "copy": copy,
        },
    )
