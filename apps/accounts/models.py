from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class CustomUser(AbstractUser):
    GENERAL = "general"
    LIBRARIAN = "librarian"

    ROLE_CHOICES = [
        (GENERAL, "一般"),
        (LIBRARIAN, "司書"),
    ]
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=GENERAL,  # デフォルトは「一般」
        verbose_name="ロール",
        help_text="ユーザーの役割を選択してください。",
    )
