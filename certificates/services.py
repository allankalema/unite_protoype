from datetime import datetime
import secrets

from django.db import IntegrityError

from courses.models import Enrollment, Lesson, LessonProgress, QuizAttempt

from .models import Certificate


def _generate_certificate_number(sequence):
    year = datetime.now().year
    return f"UNITE-MVP-{year}-{sequence:04d}"


def _next_sequence():
    last = Certificate.objects.order_by("-id").first()
    return (last.id + 1) if last else 1


def _generate_verification_code():
    return secrets.token_hex(16).upper()


def get_or_create_certificate_if_eligible(user, course):
    enrollment = Enrollment.objects.filter(user=user, course=course).first()
    if not enrollment:
        return None

    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = LessonProgress.objects.filter(
        user=user,
        lesson__module__course=course,
        is_completed=True,
    ).count()

    passed_attempt = QuizAttempt.objects.filter(
        user=user,
        quiz__course=course,
        passed=True,
        percentage__gte=course.passing_score,
    ).order_by("-percentage", "-attempted_at").first()

    if total_lessons == 0 or completed_lessons < total_lessons or not passed_attempt:
        return None

    cert = Certificate.objects.filter(user=user, course=course).first()
    if cert:
        if not cert.verification_code:
            cert.verification_code = _generate_verification_code()
            cert.save(update_fields=["verification_code"])
        return cert

    sequence = _next_sequence()
    cert_number = _generate_certificate_number(sequence)

    try:
        cert = Certificate.objects.create(
            user=user,
            course=course,
            certificate_number=cert_number,
            verification_code=_generate_verification_code(),
            final_score=passed_attempt.percentage,
        )
        enrollment.is_completed = True
        if not enrollment.completed_at:
            enrollment.completed_at = cert.issued_at
        enrollment.save(update_fields=["is_completed", "completed_at"])
        return cert
    except IntegrityError:
        return Certificate.objects.filter(user=user, course=course).first()
