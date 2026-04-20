from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ai_tutor.services import generate_lesson_summary
from certificates.services import get_or_create_certificate_if_eligible

from .models import Course, Enrollment, Lesson, LessonProgress, Quiz, QuizAttempt
from .services import (
    average_quiz_score_for_user,
    check_course_completion,
    completed_lessons_for_user,
    course_total_lessons,
    progress_percentage,
    update_enrollment_completion,
)


def _is_enrolled(user, course):
    return Enrollment.objects.filter(user=user, course=course).exists()


def _ordered_lessons_for_course(course):
    return Lesson.objects.filter(module__course=course).select_related("module", "module__course").order_by(
        "module__order", "module__id", "order", "id"
    )


def _lesson_type_label(lesson):
    return dict(Lesson.TYPE_CHOICES).get(lesson.lesson_type, lesson.lesson_type.title())


def _course_instructor_info(course):
    if not course.created_by:
        return "TBA", "UNITE"

    user = course.created_by
    instructor_name = user.username or "TBA"
    institution_name = "UNITE"

    profile = getattr(user, "profile", None)
    if profile:
        if profile.full_name:
            instructor_name = profile.full_name
        if profile.institution_name:
            institution_name = profile.institution_name
    return instructor_name, institution_name


def course_list_view(request):
    courses = Course.objects.filter(is_published=True).select_related("created_by", "created_by__profile")
    enrolled_course_ids = set()
    if request.user.is_authenticated:
        enrolled_course_ids = set(
            Enrollment.objects.filter(user=request.user).values_list("course_id", flat=True)
        )

    course_rows = []
    for course in courses:
        instructor_name, institution_name = _course_instructor_info(course)
        course_rows.append(
            {
                "course": course,
                "instructor_name": instructor_name,
                "institution_name": institution_name,
            }
        )

    return render(
        request,
        "courses/course_list.html",
        {"course_rows": course_rows, "enrolled_course_ids": enrolled_course_ids},
    )


def course_detail_view(request, slug):
    course = get_object_or_404(
        Course.objects.prefetch_related("modules__lessons").select_related("created_by", "created_by__profile"),
        slug=slug,
        is_published=True,
    )
    is_enrolled = request.user.is_authenticated and _is_enrolled(request.user, course)
    user_progress = None
    average_score = None
    instructor_name, institution_name = _course_instructor_info(course)
    if is_enrolled:
        user_progress = progress_percentage(request.user, course)
        average_score = average_quiz_score_for_user(request.user, course)

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "is_enrolled": is_enrolled,
            "user_progress": user_progress,
            "average_score": average_score,
            "instructor_name": instructor_name,
            "institution_name": institution_name,
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
        Course.objects.prefetch_related("modules__lessons", "quizzes").select_related("created_by", "created_by__profile"),
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
    instructor_name, institution_name = _course_instructor_info(course)

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
            "average_score": average_quiz_score_for_user(request.user, course),
            "instructor_name": instructor_name,
            "institution_name": institution_name,
        },
    )


@login_required
def lesson_detail_view(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("module", "module__course").prefetch_related("resources"),
        id=lesson_id,
    )
    course = lesson.module.course

    if not _is_enrolled(request.user, course):
        messages.warning(request, "Enroll in this course to access lessons.")
        return redirect("courses:detail", slug=course.slug)

    progress_obj, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

    lesson_sequence = list(_ordered_lessons_for_course(course).values_list("id", flat=True))
    index = lesson_sequence.index(lesson.id)
    prev_lesson_id = lesson_sequence[index - 1] if index > 0 else None
    next_lesson_id = lesson_sequence[index + 1] if index < len(lesson_sequence) - 1 else None
    modules = course.modules.prefetch_related("lessons").all()

    return render(
        request,
        "courses/lesson_detail.html",
        {
            "lesson": lesson,
            "course": course,
            "progress_obj": progress_obj,
            "prev_lesson_id": prev_lesson_id,
            "next_lesson_id": next_lesson_id,
            "modules": modules,
            "lesson_type_label": _lesson_type_label(lesson),
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

    check_course_completion(request.user, course)
    update_enrollment_completion(request.user, course)
    get_or_create_certificate_if_eligible(request.user, course)

    messages.success(request, "Lesson marked as complete.")
    return redirect("courses:lesson-detail", lesson_id=lesson_id)


@login_required
def summarize_lesson_view(request, lesson_id):
    if request.method != "POST":
        return redirect("courses:lesson-detail", lesson_id=lesson_id)

    lesson = get_object_or_404(Lesson.objects.select_related("module", "module__course"), id=lesson_id)
    course = lesson.module.course
    if not _is_enrolled(request.user, course):
        messages.error(request, "You are not enrolled in this course.")
        return redirect("courses:detail", slug=course.slug)

    summary = generate_lesson_summary(lesson)
    if summary.startswith("AI tutor"):
        messages.error(request, summary)
        return redirect("courses:lesson-detail", lesson_id=lesson_id)

    ai_keywords = ""
    if "Keywords:" in summary:
        parts = summary.split("Keywords:", 1)
        lesson.ai_summary = parts[0].strip()
        ai_keywords = parts[1].strip()
    else:
        lesson.ai_summary = summary
    lesson.ai_keywords = ai_keywords
    lesson.save(update_fields=["ai_summary", "ai_keywords"])
    messages.success(request, "AI lesson summary generated.")
    return redirect("courses:lesson-detail", lesson_id=lesson_id)


@login_required
def quiz_detail_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related("questions").select_related("course"), id=quiz_id, is_active=True)
    if not _is_enrolled(request.user, quiz.course):
        messages.warning(request, "Please enroll in this course first.")
        return redirect("courses:detail", slug=quiz.course.slug)

    attempts_count = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
    latest_attempt = QuizAttempt.objects.filter(user=request.user, quiz=quiz).first()
    attempts_remaining = max(quiz.max_attempts - attempts_count, 0)
    limit_reached = attempts_remaining == 0
    return render(
        request,
        "courses/quiz_detail.html",
        {
            "quiz": quiz,
            "latest_attempt": latest_attempt,
            "attempts_count": attempts_count,
            "attempts_remaining": attempts_remaining,
            "limit_reached": limit_reached,
        },
    )


@login_required
def submit_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related("questions").select_related("course"), id=quiz_id, is_active=True)

    if request.method != "POST":
        return redirect("courses:quiz-detail", quiz_id=quiz.id)

    if not _is_enrolled(request.user, quiz.course):
        messages.warning(request, "Please enroll in this course first.")
        return redirect("courses:detail", slug=quiz.course.slug)

    attempts_count = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
    if attempts_count >= quiz.max_attempts:
        messages.warning(request, "You have reached the maximum number of attempts for this quiz.")
        return redirect("courses:quiz-detail", quiz_id=quiz.id)

    questions = list(quiz.questions.all())
    total_questions = len(questions)
    if total_questions == 0:
        messages.error(request, "Quiz has no questions configured yet.")
        return redirect("courses:quiz-detail", quiz_id=quiz.id)

    score = 0
    review_rows = []
    for question in questions:
        selected = request.POST.get(f"question_{question.id}")
        is_correct = selected == question.correct_option
        if is_correct:
            score += 1
        review_rows.append(
            {
                "question": question,
                "selected": selected,
                "is_correct": is_correct,
                "correct_option": question.correct_option,
                "explanation": question.explanation,
            }
        )

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

    check_course_completion(request.user, quiz.course)
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
            "review_rows": review_rows,
            "attempts_count": attempts_count + 1,
            "attempts_remaining": max(quiz.max_attempts - (attempts_count + 1), 0),
            "limit_reached": (attempts_count + 1) >= quiz.max_attempts,
        },
    )
