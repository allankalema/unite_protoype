from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("certificates/", views.my_certificates_view, name="my-certificates"),
    path("certificates/<int:certificate_id>/", views.certificate_detail_view, name="detail"),
    path("certificates/verify/<str:code>/", views.verify_certificate_view, name="verify"),
]
