from django.db import models


# Create your models here.
class Book(models.Model):
    isbn = models.CharField(max_length=13, unique=True, verbose_name="ISBN")
    title = models.CharField(max_length=255, verbose_name="タイトル")
    author = models.CharField(max_length=255, verbose_name="著者")
    publisher = models.CharField(max_length=255, verbose_name="出版社")
    published_date = models.DateField(verbose_name="出版日")
    image_url = models.URLField(blank=True, verbose_name="画像用リンク")
    edition = models.PositiveIntegerField(default=1, verbose_name="版数")

    def __str__(self):
        return f"{self.title}（第{self.edition}版）"

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
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="書籍")
    location = models.ForeignKey(
        StorageLocation, on_delete=models.CASCADE, verbose_name="保存場所"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("available", "貸出可能"),
            ("loaned", "貸出中"),
            ("lost", "廃棄済み"),
        ],
        verbose_name="ステータス",
    )
    registered_date = models.DateField(auto_now_add=True, verbose_name="登録日")

    class Meta:
        verbose_name = "蔵書"
        verbose_name_plural = "蔵書"
