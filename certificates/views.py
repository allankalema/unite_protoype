from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Certificate


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
    return render(request, "certificates/certificate_detail.html", {"certificate": certificate})
