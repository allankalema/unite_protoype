from django import template
from django.urls import NoReverseMatch, reverse

from ai_tutor.models import ChatSession
from certificates.models import Certificate
from courses.models import Course, Lesson, Quiz

register = template.Library()


def _safe_reverse(name, **kwargs):
    try:
        return reverse(name, kwargs=kwargs) if kwargs else reverse(name)
    except NoReverseMatch:
        return ""


def _label_for_dashboard(view_name):
    labels = {
        "dashboard:home": "Staff Dashboard",
        "dashboard:manage-courses": "Manage Courses",
        "dashboard:course-detail": "Course Record",
        "dashboard:create-course": "Create Course",
        "dashboard:edit-course": "Edit Course",
        "dashboard:delete-course": "Delete Course",
        "dashboard:manage-modules": "Manage Modules",
        "dashboard:module-detail": "Module Record",
        "dashboard:create-module": "Create Module",
        "dashboard:edit-module": "Edit Module",
        "dashboard:delete-module": "Delete Module",
        "dashboard:manage-lessons": "Manage Lessons",
        "dashboard:lesson-detail": "Lesson Record",
        "dashboard:create-lesson": "Create Lesson",
        "dashboard:edit-lesson": "Edit Lesson",
        "dashboard:delete-lesson": "Delete Lesson",
        "dashboard:manage-resources": "Manage Resources",
        "dashboard:resource-detail": "Resource Record",
        "dashboard:create-resource": "Create Resource",
        "dashboard:edit-resource": "Edit Resource",
        "dashboard:delete-resource": "Delete Resource",
        "dashboard:manage-quizzes": "Manage Quizzes",
        "dashboard:create-quiz": "Create Quiz",
        "dashboard:edit-quiz": "Edit Quiz",
        "dashboard:delete-quiz": "Delete Quiz",
        "dashboard:create-question": "Create Question",
        "dashboard:edit-question": "Edit Question",
        "dashboard:delete-question": "Delete Question",
        "dashboard:enrollments": "Enrollments",
        "dashboard:enrollment-detail": "Enrollment Record",
        "dashboard:ai-logs": "AI Logs",
    }
    return labels.get(view_name, "Dashboard")


@register.simple_tag(takes_context=True)
def get_breadcrumbs(context):
    request = context.get("request")
    if not request or not getattr(request, "resolver_match", None):
        return []

    match = request.resolver_match
    view_name = match.view_name
    kwargs = match.kwargs or {}

    crumbs = [{"label": "Home", "url": _safe_reverse("core:home")}]

    if view_name == "core:home":
        return crumbs
    if view_name == "core:about":
        crumbs.append({"label": "About", "url": ""})
        return crumbs

    if view_name == "accounts:login":
        crumbs.append({"label": "Login", "url": ""})
        return crumbs
    if view_name == "accounts:register":
        crumbs.append({"label": "Register", "url": ""})
        return crumbs
    if view_name == "accounts:profile":
        crumbs.append({"label": "Profile", "url": ""})
        return crumbs

    if view_name == "courses:list":
        crumbs.append({"label": "Courses", "url": ""})
        return crumbs
    if view_name == "courses:my-courses":
        crumbs.append({"label": "My Courses", "url": ""})
        return crumbs

    if view_name in {"courses:detail", "courses:learn"}:
        slug = kwargs.get("slug")
        course = Course.objects.only("title", "slug").filter(slug=slug).first()
        crumbs.append({"label": "Courses", "url": _safe_reverse("courses:list")})
        if course:
            crumbs.append({"label": course.title, "url": _safe_reverse("courses:detail", slug=course.slug)})
        if view_name == "courses:learn":
            crumbs.append({"label": "Learning", "url": ""})
        return crumbs

    if view_name in {"courses:lesson-detail", "courses:lesson-complete", "courses:lesson-summarize"}:
        lesson_id = kwargs.get("lesson_id")
        lesson = (
            Lesson.objects.select_related("module", "module__course")
            .only("id", "title", "module__course__title", "module__course__slug")
            .filter(id=lesson_id)
            .first()
        )
        crumbs.append({"label": "Courses", "url": _safe_reverse("courses:list")})
        if lesson:
            course = lesson.module.course
            crumbs.append({"label": course.title, "url": _safe_reverse("courses:detail", slug=course.slug)})
            crumbs.append({"label": "Learning", "url": _safe_reverse("courses:learn", slug=course.slug)})
            crumbs.append({"label": lesson.title, "url": ""})
        return crumbs

    if view_name in {"courses:quiz-detail", "courses:quiz-submit"}:
        quiz_id = kwargs.get("quiz_id")
        quiz = Quiz.objects.select_related("course").only("id", "title", "course__title", "course__slug").filter(id=quiz_id).first()
        crumbs.append({"label": "Courses", "url": _safe_reverse("courses:list")})
        if quiz:
            crumbs.append({"label": quiz.course.title, "url": _safe_reverse("courses:detail", slug=quiz.course.slug)})
            crumbs.append({"label": "Learning", "url": _safe_reverse("courses:learn", slug=quiz.course.slug)})
            crumbs.append({"label": quiz.title, "url": ""})
        return crumbs

    if view_name == "ai_tutor:history":
        crumbs.append({"label": "AI Tutor History", "url": ""})
        return crumbs

    if view_name == "ai_tutor:chat":
        crumbs.append({"label": "AI Tutor", "url": ""})
        session_id = request.GET.get("session_id")
        lesson_id = request.GET.get("lesson_id")
        course_id = request.GET.get("course_id")
        session = None
        if session_id:
            session = ChatSession.objects.select_related("course", "lesson").filter(id=session_id).first()
            if session and session.course:
                crumbs.append({"label": session.course.title, "url": _safe_reverse("courses:detail", slug=session.course.slug)})
            if session and session.lesson:
                crumbs.append({"label": session.lesson.title, "url": ""})
            return crumbs
        if lesson_id:
            lesson = Lesson.objects.select_related("module", "module__course").filter(id=lesson_id).first()
            if lesson:
                crumbs.append({"label": lesson.module.course.title, "url": _safe_reverse("courses:detail", slug=lesson.module.course.slug)})
                crumbs.append({"label": lesson.title, "url": ""})
            return crumbs
        if course_id:
            course = Course.objects.only("title", "slug").filter(id=course_id).first()
            if course:
                crumbs.append({"label": course.title, "url": _safe_reverse("courses:detail", slug=course.slug)})
            return crumbs
        return crumbs

    if view_name == "certificates:my-certificates":
        crumbs.append({"label": "Certificates", "url": ""})
        return crumbs

    if view_name == "certificates:detail":
        certificate_id = kwargs.get("certificate_id")
        cert = (
            Certificate.objects.select_related("course")
            .only("id", "course__title", "course__slug")
            .filter(id=certificate_id)
            .first()
        )
        crumbs.append({"label": "Certificates", "url": _safe_reverse("certificates:my-certificates")})
        if cert:
            crumbs.append({"label": cert.course.title, "url": _safe_reverse("courses:detail", slug=cert.course.slug)})
        crumbs.append({"label": "Certificate Detail", "url": ""})
        return crumbs

    if view_name == "certificates:verify":
        crumbs.append({"label": "Certificate Verification", "url": ""})
        return crumbs

    if view_name.startswith("dashboard:"):
        crumbs.append({"label": "Staff Dashboard", "url": _safe_reverse("dashboard:home")})
        if view_name != "dashboard:home":
            crumbs.append({"label": _label_for_dashboard(view_name), "url": ""})
        return crumbs

    return crumbs
