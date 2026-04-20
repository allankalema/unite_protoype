from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_TEACHER = "teacher"
    ROLE_STAFF = "staff"
    ROLE_CHOICES = [
        (ROLE_TEACHER, "Teacher"),
        (ROLE_STAFF, "Staff"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    institution_name = models.CharField(max_length=255, blank=True)
    district = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_TEACHER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.role})"
