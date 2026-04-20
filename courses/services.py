from django.utils import timezone

from courses.models import Enrollment, LessonProgress, QuizAttempt


def course_total_lessons(course):
    return sum(module.lessons.count() for module in course.modules.all())


def completed_lessons_for_user(user, course):
    return LessonProgress.objects.filter(
        user=user,
        lesson__module__course=course,
        is_completed=True,
    ).count()


def progress_percentage(user, course):
    total = course_total_lessons(course)
    if total == 0:
        return 0
    completed = completed_lessons_for_user(user, course)
    return int((completed / total) * 100)


def update_enrollment_completion(user, course):
    enrollment = Enrollment.objects.filter(user=user, course=course).first()
    if not enrollment:
        return None

    should_complete = check_course_completion(user, course)
    if should_complete and not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=["is_completed", "completed_at"])
    elif not should_complete and enrollment.is_completed:
        enrollment.is_completed = False
        enrollment.completed_at = None
        enrollment.save(update_fields=["is_completed", "completed_at"])
    return enrollment


def check_course_completion(user, course):
    total = course_total_lessons(course)
    completed = completed_lessons_for_user(user, course)
    has_passed_quiz = QuizAttempt.objects.filter(
        user=user,
        quiz__course=course,
        passed=True,
    ).exists()
    return total > 0 and completed >= total and has_passed_quiz


def average_quiz_score_for_user(user, course):
    attempts = QuizAttempt.objects.filter(user=user, quiz__course=course)
    if not attempts.exists():
        return 0.0
    return round(sum(item.percentage for item in attempts) / attempts.count(), 2)


def completion_rate_percentage():
    total = Enrollment.objects.count()
    if total == 0:
        return 0
    completed = Enrollment.objects.filter(is_completed=True).count()
    return round((completed / total) * 100, 2)
