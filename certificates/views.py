from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Certificate


def _first_last_name(user):
    profile = getattr(user, "profile", None)
    full_name = ""
    if profile and profile.full_name:
        full_name = profile.full_name.strip()
    if not full_name:
        full_name = user.get_full_name().strip()

    parts = [part for part in full_name.split() if part]
    if len(parts) >= 2:
        return f"{parts[0]} {parts[-1]}"
    if user.first_name and user.last_name:
        return f"{user.first_name.strip()} {user.last_name.strip()}".strip()
    if len(parts) == 1:
        return parts[0]
    return "Name Not Set"


def _level_theme(level):
    # Palette-only theme mapping.
    themes = {
        "beginner": {
            "outer_border": "border-unite-blue-500",
            "inner_border": "border-unite-blue-500",
            "corner_border": "border-unite-blue-500",
            "title_text": "text-unite-navy-500",
            "badge_bg": "bg-unite-blue-100",
            "badge_text": "text-unite-blue-600",
            "seal_border": "border-unite-blue-500",
            "seal_bg": "bg-unite-blue-100",
            "seal_text": "text-unite-blue-600",
        },
        "intermediate": {
            "outer_border": "border-unite-orange-500",
            "inner_border": "border-unite-orange-500",
            "corner_border": "border-unite-orange-500",
            "title_text": "text-unite-navy-500",
            "badge_bg": "bg-unite-orange-100",
            "badge_text": "text-unite-orange-600",
            "seal_border": "border-unite-orange-500",
            "seal_bg": "bg-unite-orange-100",
            "seal_text": "text-unite-orange-600",
        },
        "advanced": {
            "outer_border": "border-unite-navy-500",
            "inner_border": "border-unite-navy-500",
            "corner_border": "border-unite-navy-500",
            "title_text": "text-unite-navy-500",
            "badge_bg": "bg-unite-gray-100",
            "badge_text": "text-unite-navy-500",
            "seal_border": "border-unite-navy-500",
            "seal_bg": "bg-unite-gray-100",
            "seal_text": "text-unite-navy-500",
        },
    }
    return themes.get(level or "beginner", themes["beginner"])


@login_required
def my_certificates_view(request):
    certificates = Certificate.objects.filter(user=request.user).select_related("course")
    return render(request, "certificates/my_certificates.html", {"certificates": certificates})


@login_required
def certificate_detail_view(request, certificate_id):
    certificate = get_object_or_404(
        Certificate.objects.select_related("course", "user", "user__profile"),
        id=certificate_id,
        user=request.user,
    )
    base_url = (settings.SITE_URL or "").rstrip("/") + "/"
    verify_path = reverse("certificates:verify", kwargs={"code": certificate.verification_code})
    verify_url = urljoin(base_url, verify_path.lstrip("/")) if base_url else verify_path

    context = {
        "certificate": certificate,
        "recipient_name": _first_last_name(certificate.user),
        "certificate_level": certificate.course.get_level_display(),
        "theme": _level_theme(certificate.course.level),
        "verify_url": verify_url,
    }
    return render(request, "certificates/certificate_detail.html", context)


def verify_certificate_view(request, code):
    certificate = Certificate.objects.filter(verification_code=code).select_related("course", "user", "user__profile").first()
    context = {"certificate": certificate, "code": code}
    if certificate:
        base_url = (settings.SITE_URL or "").rstrip("/") + "/"
        verify_path = reverse("certificates:verify", kwargs={"code": certificate.verification_code})
        verify_url = urljoin(base_url, verify_path.lstrip("/")) if base_url else verify_path
        context.update(
            {
                "recipient_name": _first_last_name(certificate.user),
                "certificate_level": certificate.course.get_level_display(),
                "theme": _level_theme(certificate.course.level),
                "verify_url": verify_url,
            }
        )
    return render(request, "certificates/verify.html", context)
