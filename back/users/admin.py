from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "phone", "is_staff", "is_active", "date_joined")
    ordering = ("email",)
    search_fields = ("email", "username", "phone")

    fieldsets = UserAdmin.fieldsets + (
        ("Contact", {"fields": ("phone",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "phone", "password1", "password2"),
            },
        ),
    )
