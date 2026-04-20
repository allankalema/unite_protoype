from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "verification_code", "user", "course", "final_score", "issued_at")
    search_fields = ("certificate_number", "verification_code", "user__username", "course__title")
