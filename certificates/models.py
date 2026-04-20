from django.contrib.auth.models import User
from django.db import models

from courses.models import Course


class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    certificate_number = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    final_score = models.FloatField(default=0)

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.certificate_number} - {self.user.username}"
