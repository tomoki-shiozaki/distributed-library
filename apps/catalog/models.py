from django.core.exceptions import ValidationError
from django.db import models


# Create your models here.
class Book(models.Model):
    class PublishedDatePrecision(models.TextChoices):
        UNKNOWN = "unknown", "不明"
        YEAR = "year", "年"
        MONTH = "month", "年月"
        DAY = "day", "年月日"

    isbn = models.CharField(
        max_length=13,
        unique=True,
        verbose_name="ISBN",
        help_text="13桁の数字をハイフンなしで入力してください。",
    )
    title = models.CharField(max_length=255, verbose_name="タイトル")
    author = models.CharField(max_length=255, verbose_name="著者")
    publisher = models.CharField(
        max_length=255,
        verbose_name="出版社",
        blank=True,
        help_text="出版社が不明な場合は空欄にしてもかまいません。",
    )
    published_date = models.DateField(
        verbose_name="出版日",
        help_text="YYYY-MM-DDの形式で入力してください。例：2025-01-01",
        blank=True,
        null=True,
    )
    published_date_precision = models.CharField(
        max_length=10,
        choices=PublishedDatePrecision.choices,
        default=PublishedDatePrecision.UNKNOWN,
        verbose_name="出版日の精度",
        help_text=(
            "出版日がどこまで正確に分かっているかを選択してください。<br><br>"
            "例：<br>"
            "- APIで年月日まで取得できた場合 → 「年月日」の精度が自動設定されます。<br>"
            "- APIで年月のみ、または年のみ取得できた場合 → 「年月」や「年」の精度が設定されます。<br>"
            "　※この場合、月や日は「1」に自動補完されています。<br><br>"
            "正確な出版日が判明した場合は、出版日と精度を「年月日」に更新してください。<br>"
            "出版日が完全に不明な場合は、「不明」を選択してください。"
        ),
    )
    image_url = models.URLField(
        blank=True,
        verbose_name="画像用リンク",
        help_text="書籍のカバー画像のURLを入力してください（任意）。",
    )
    edition = models.PositiveIntegerField(
        verbose_name="版数",
        blank=True,
        null=True,
        help_text="任意で数値を入力してください。例えば第2版なら「2」と入力してください。わからなければ空欄のままで構いません。",
    )
    description = models.TextField(
        verbose_name="内容紹介",
        blank=True,
        help_text="本の概要や見どころなどを、利用者向けに簡単に説明してください（任意）。",
    )

    def clean(self):
        # 出版日がNoneの場合に精度が不明でない場合はエラー
        if (
            not self.published_date
            and self.published_date_precision != Book.PublishedDatePrecision.UNKNOWN
        ):
            raise ValidationError(
                "出版日が未入力の場合、精度は「不明」に設定してください。"
            )
        # 出版日が入力されている場合、精度が「不明」でないことを確認
        elif (
            self.published_date
            and self.published_date_precision == Book.PublishedDatePrecision.UNKNOWN
        ):
            raise ValidationError(
                "出版日が入力されている場合は、精度を「不明」以外のいずれかに選択してください。"
            )

    def __str__(self):
        if self.edition:
            return f"{self.title}（第{self.edition}版）"
        return self.title

    class Meta:
        verbose_name = "本"
        verbose_name_plural = "本マスター"


class StorageLocation(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "保存場所"
        verbose_name_plural = "保存場所マスター"


class Copy(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "貸出可能"
        LOANED = "loaned", "貸出中"
        DISCARDED = "discarded", "廃棄済み"

    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="copies", verbose_name="書籍"
    )
    location = models.ForeignKey(
        StorageLocation, on_delete=models.CASCADE, verbose_name="保存場所"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        verbose_name="状態",
    )
    registered_date = models.DateField(auto_now_add=True, verbose_name="登録日")

    def __str__(self):
        return f"{self.book} - {self.location.name} - {self.get_status_display()}"

    class Meta:
        verbose_name = "蔵書"
        verbose_name_plural = "蔵書"
