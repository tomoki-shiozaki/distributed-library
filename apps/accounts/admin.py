from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


# Register your models here.
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        "email",
        "username",
        "role",
        "is_staff",
    ]
    fieldsets = UserAdmin.fieldsets + (("カスタムフィールド", {"fields": ("role",)}),)

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("カスタムフィールド", {"fields": ("role",)}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
