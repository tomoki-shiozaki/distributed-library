from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class CustomUser(AbstractUser):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    LEVEL_CHOICES = [
        (BEGINNER, "初心者"),
        (INTERMEDIATE, "中級者"),
        (ADVANCED, "上級者"),
    ]
    level = models.CharField(
        max_length=15,
        choices=LEVEL_CHOICES,
        default=BEGINNER,  # デフォルトは「初心者」
        verbose_name="レベル",
    )
