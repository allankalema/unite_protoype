from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "user", "course", "final_score", "issued_at")
    search_fields = ("certificate_number", "user__username", "course__title")
