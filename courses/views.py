from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from certificates.services import get_or_create_certificate_if_eligible

from .models import Course, Enrollment, Lesson, LessonProgress, Quiz, QuizAttempt
from .services import completed_lessons_for_user, course_total_lessons, progress_percentage, update_enrollment_completion


def _is_enrolled(user, course):
    return Enrollment.objects.filter(user=user, course=course).exists()


def _ordered_lessons_for_course(course):
    return Lesson.objects.filter(module__course=course).select_related("module", "module__course").order_by(
        "module__order", "module__id", "order", "id"
    )


def course_list_view(request):
    courses = Course.objects.filter(is_published=True)
    enrolled_course_ids = set()
    if request.user.is_authenticated:
        enrolled_course_ids = set(
            Enrollment.objects.filter(user=request.user).values_list("course_id", flat=True)
        )

    return render(
        request,
        "courses/course_list.html",
        {"courses": courses, "enrolled_course_ids": enrolled_course_ids},
    )


def course_detail_view(request, slug):
    course = get_object_or_404(Course.objects.prefetch_related("modules__lessons"), slug=slug, is_published=True)
    is_enrolled = request.user.is_authenticated and _is_enrolled(request.user, course)

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "is_enrolled": is_enrolled,
        },
    )


@login_required
def enroll_course_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)

    if created:
        messages.success(request, f"You are now enrolled in {course.title}.")
    else:
        messages.info(request, "You are already enrolled in this course.")

    return redirect("courses:learn", slug=course.slug)


@login_required
def my_courses_view(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related("course")
    enrollment_rows = [{"enrollment": e, "progress": progress_percentage(request.user, e.course)} for e in enrollments]
    return render(request, "courses/my_courses.html", {"enrollment_rows": enrollment_rows})


@login_required
def course_learn_view(request, slug):
    course = get_object_or_404(
        Course.objects.prefetch_related("modules__lessons", "quizzes"),
        slug=slug,
    )

    if not _is_enrolled(request.user, course):
        messages.warning(request, "Please enroll in the course first.")
        return redirect("courses:detail", slug=course.slug)

    lessons = _ordered_lessons_for_course(course)
    completed_ids = set(
        LessonProgress.objects.filter(
            user=request.user,
            lesson__in=lessons,
            is_completed=True,
        ).values_list("lesson_id", flat=True)
    )

    progress = progress_percentage(request.user, course)
    certificate = get_or_create_certificate_if_eligible(request.user, course)

    return render(
        request,
        "courses/course_learn.html",
        {
            "course": course,
            "completed_ids": completed_ids,
            "progress": progress,
            "total_lessons": course_total_lessons(course),
            "completed_lessons": completed_lessons_for_user(request.user, course),
            "certificate": certificate,
        },
    )


@login_required
def lesson_detail_view(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related("module", "module__course"), id=lesson_id)
    course = lesson.module.course

    if not _is_enrolled(request.user, course):
        messages.warning(request, "Enroll in this course to access lessons.")
        return redirect("courses:detail", slug=course.slug)

    progress_obj, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

    lesson_sequence = list(_ordered_lessons_for_course(course).values_list("id", flat=True))
    index = lesson_sequence.index(lesson.id)
    prev_lesson_id = lesson_sequence[index - 1] if index > 0 else None
    next_lesson_id = lesson_sequence[index + 1] if index < len(lesson_sequence) - 1 else None

    return render(
        request,
        "courses/lesson_detail.html",
        {
            "lesson": lesson,
            "course": course,
            "progress_obj": progress_obj,
            "prev_lesson_id": prev_lesson_id,
            "next_lesson_id": next_lesson_id,
        },
    )


@login_required
def mark_lesson_complete_view(request, lesson_id):
    if request.method != "POST":
        return redirect("courses:lesson-detail", lesson_id=lesson_id)

    lesson = get_object_or_404(Lesson.objects.select_related("module", "module__course"), id=lesson_id)
    course = lesson.module.course

    if not _is_enrolled(request.user, course):
        messages.error(request, "You are not enrolled in this course.")
        return redirect("courses:detail", slug=course.slug)

    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.save(update_fields=["is_completed", "completed_at"])

    update_enrollment_completion(request.user, course)
    get_or_create_certificate_if_eligible(request.user, course)

    messages.success(request, "Lesson marked as complete.")
    return redirect("courses:lesson-detail", lesson_id=lesson_id)


@login_required
def quiz_detail_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related("questions").select_related("course"), id=quiz_id, is_active=True)
    if not _is_enrolled(request.user, quiz.course):
        messages.warning(request, "Please enroll in this course first.")
        return redirect("courses:detail", slug=quiz.course.slug)

    latest_attempt = QuizAttempt.objects.filter(user=request.user, quiz=quiz).first()
    return render(
        request,
        "courses/quiz_detail.html",
        {"quiz": quiz, "latest_attempt": latest_attempt},
    )


@login_required
def submit_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related("questions").select_related("course"), id=quiz_id, is_active=True)

    if request.method != "POST":
        return redirect("courses:quiz-detail", quiz_id=quiz.id)

    if not _is_enrolled(request.user, quiz.course):
        messages.warning(request, "Please enroll in this course first.")
        return redirect("courses:detail", slug=quiz.course.slug)

    questions = list(quiz.questions.all())
    total_questions = len(questions)
    if total_questions == 0:
        messages.error(request, "Quiz has no questions configured yet.")
        return redirect("courses:quiz-detail", quiz_id=quiz.id)

    score = 0
    for question in questions:
        selected = request.POST.get(f"question_{question.id}")
        if selected == question.correct_option:
            score += 1

    percentage = round((score / total_questions) * 100, 2)
    passed = percentage >= quiz.course.passing_score

    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        passed=passed,
    )

    update_enrollment_completion(request.user, quiz.course)
    certificate = get_or_create_certificate_if_eligible(request.user, quiz.course)

    if passed:
        messages.success(request, f"Great job. You scored {percentage}% and passed.")
    else:
        messages.warning(request, f"You scored {percentage}%. You need {quiz.course.passing_score}% to pass.")

    return render(
        request,
        "courses/quiz_detail.html",
        {
            "quiz": quiz,
            "latest_attempt": attempt,
            "show_result": True,
            "certificate": certificate,
        },
    )
