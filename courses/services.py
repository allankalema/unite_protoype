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

    total = course_total_lessons(course)
    completed = completed_lessons_for_user(user, course)
    has_passed_quiz = QuizAttempt.objects.filter(
        user=user,
        quiz__course=course,
        passed=True,
        percentage__gte=course.passing_score,
    ).exists()

    should_complete = total > 0 and completed >= total and has_passed_quiz
    if should_complete and not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=["is_completed", "completed_at"])
    return enrollment
