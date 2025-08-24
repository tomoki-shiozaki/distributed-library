from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser


# Register your models here.
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
    ]
    fieldsets = UserAdmin.fieldsets + (("追加情報", {"fields": ("role",)}),)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    list_filter = ("role", "is_active", "is_staff")


admin.site.register(CustomUser, CustomUserAdmin)
