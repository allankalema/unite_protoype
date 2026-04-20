from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "role", "institution_name", "district", "created_at")
    list_filter = ("role", "district", "created_at")
    search_fields = ("full_name", "email", "user__username")
