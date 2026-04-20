from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import staff_required
from ai_tutor.models import ChatMessage, ChatSession
from certificates.models import Certificate
from courses.forms import CourseForm, LessonForm, LessonResourceForm, ModuleForm, QuestionForm, QuizForm
from courses.models import Course, Enrollment, Lesson, LessonResource, Module, Question, Quiz
from courses.services import completion_rate_percentage

COURSE_WIZARD_STEPS = [
    {
        "title": "Core Details",
        "description": "Define the core course identity and academic positioning.",
        "fields": ["title", "slug", "category", "level", "created_by", "is_published"],
    },
    {
        "title": "Learning Content",
        "description": "Provide learner-facing descriptions and outcomes.",
        "fields": ["short_description", "description", "learning_objectives", "prerequisites", "target_audience"],
    },
    {
        "title": "Delivery Settings",
        "description": "Configure assessment and delivery settings.",
        "fields": ["cover_image", "passing_score", "estimated_duration_hours"],
    },
]

MODULE_WIZARD_STEPS = [
    {
        "title": "Module Basics",
        "description": "Select course and define module position.",
        "fields": ["course", "title", "order"],
    },
    {
        "title": "Module Description",
        "description": "Add extra context for instructors and learners.",
        "fields": ["description"],
    },
]

LESSON_WIZARD_STEPS = [
    {
        "title": "Lesson Setup",
        "description": "Attach lesson to module and define lesson metadata.",
        "fields": ["module", "title", "order", "lesson_type", "duration_minutes"],
    },
    {
        "title": "Learning Content",
        "description": "Add main lesson content and supporting summaries.",
        "fields": ["content", "summary", "ai_summary", "ai_keywords"],
    },
    {
        "title": "Media and Downloads",
        "description": "Attach optional external video or downloadable links.",
        "fields": ["video_url", "downloadable_material_url"],
    },
]

RESOURCE_WIZARD_STEPS = [
    {
        "title": "Resource Identity",
        "description": "Define what this resource is and where it belongs.",
        "fields": ["lesson", "title", "resource_type"],
    },
    {
        "title": "Resource Link",
        "description": "Add the file URL or external link.",
        "fields": ["file_url"],
    },
]

QUIZ_WIZARD_STEPS = [
    {
        "title": "Quiz Basics",
        "description": "Define quiz title and course association.",
        "fields": ["course", "title"],
    },
    {
        "title": "Quiz Rules",
        "description": "Set attempts and activation behavior.",
        "fields": ["description", "is_active", "max_attempts"],
    },
]

QUESTION_WIZARD_STEPS = [
    {
        "title": "Question Prompt",
        "description": "Define the quiz and question statement.",
        "fields": ["quiz", "text"],
    },
    {
        "title": "Answer Options",
        "description": "Provide all options and select the correct one.",
        "fields": ["option_a", "option_b", "option_c", "option_d", "correct_option"],
    },
    {
        "title": "Explanation",
        "description": "Optional pedagogical explanation for answer review.",
        "fields": ["explanation"],
    },
]


def _render_wizard_form(request, form, title, wizard_steps, back_url_name):
    return render(
        request,
        "dashboard/form_wizard.html",
        {
            "form": form,
            "title": title,
            "wizard_steps": wizard_steps,
            "back_url_name": back_url_name,
        },
    )


def _apply_course_creator_permissions(form, user):
    if user.is_superuser:
        return
    form.fields.pop("created_by", None)


@staff_required
def dashboard_home_view(request):
    total_users = User.objects.count()
    total_teachers = User.objects.filter(profile__role="teacher").count()
    total_courses = Course.objects.count()
    total_enrollments = Enrollment.objects.count()
    completed_enrollments = Enrollment.objects.filter(is_completed=True).count()
    completion_rate = completion_rate_percentage()
    certificates_issued = Certificate.objects.count()
    total_ai_sessions = ChatSession.objects.count()
    total_ai_messages = ChatMessage.objects.count()

    context = {
        "total_users": total_users,
        "total_teachers": total_teachers,
        "total_courses": total_courses,
        "total_enrollments": total_enrollments,
        "completed_enrollments": completed_enrollments,
        "completion_rate": completion_rate,
        "certificates_issued": certificates_issued,
        "total_ai_sessions": total_ai_sessions,
        "total_ai_messages": total_ai_messages,
        "recent_enrollments": Enrollment.objects.select_related("user", "course")[:8],
        "recent_completions": Enrollment.objects.filter(is_completed=True).select_related("user", "course")[:8],
        "recent_certificates": Certificate.objects.select_related("user", "course")[:8],
        "recent_sessions": ChatSession.objects.select_related("user", "course", "lesson")[:8],
    }
    return render(request, "dashboard/home.html", context)


@staff_required
def manage_courses_view(request):
    courses = Course.objects.all()
    return render(request, "dashboard/manage_courses.html", {"courses": courses})


@staff_required
def course_detail_admin_view(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("created_by", "created_by__profile").prefetch_related("modules", "quizzes"),
        id=course_id,
    )
    return render(request, "dashboard/course_detail.html", {"course": course})


@staff_required
def create_course_view(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        _apply_course_creator_permissions(form, request.user)
        if form.is_valid():
            course = form.save(commit=False)
            if not course.created_by_id:
                course.created_by = request.user
            course.save()
            messages.success(request, "Course created successfully.")
            return redirect("dashboard:manage-courses")
    else:
        form = CourseForm(initial={"created_by": request.user.id})
        _apply_course_creator_permissions(form, request.user)
    return _render_wizard_form(request, form, "Create Course", COURSE_WIZARD_STEPS, "dashboard:manage-courses")


@staff_required
def edit_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        _apply_course_creator_permissions(form, request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect("dashboard:manage-courses")
    else:
        form = CourseForm(instance=course)
        _apply_course_creator_permissions(form, request.user)
    return _render_wizard_form(request, form, "Edit Course", COURSE_WIZARD_STEPS, "dashboard:manage-courses")


@staff_required
def delete_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        course.delete()
        messages.success(request, "Course deleted.")
        return redirect("dashboard:manage-courses")
    return render(request, "dashboard/confirm_delete.html", {"item": course, "back_url": "dashboard:manage-courses"})


@staff_required
def manage_modules_view(request):
    modules = Module.objects.select_related("course")
    return render(request, "dashboard/manage_modules.html", {"modules": modules})


@staff_required
def module_detail_admin_view(request, module_id):
    module = get_object_or_404(
        Module.objects.select_related("course", "course__created_by", "course__created_by__profile").prefetch_related("lessons"),
        id=module_id,
    )
    return render(request, "dashboard/module_detail.html", {"module": module})


@staff_required
def create_module_view(request):
    if request.method == "POST":
        form = ModuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Module created.")
            return redirect("dashboard:manage-modules")
    else:
        form = ModuleForm()
    return _render_wizard_form(request, form, "Create Module", MODULE_WIZARD_STEPS, "dashboard:manage-modules")


@staff_required
def edit_module_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if request.method == "POST":
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, "Module updated.")
            return redirect("dashboard:manage-modules")
    else:
        form = ModuleForm(instance=module)
    return _render_wizard_form(request, form, "Edit Module", MODULE_WIZARD_STEPS, "dashboard:manage-modules")


@staff_required
def delete_module_view(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if request.method == "POST":
        module.delete()
        messages.success(request, "Module deleted.")
        return redirect("dashboard:manage-modules")
    return render(request, "dashboard/confirm_delete.html", {"item": module, "back_url": "dashboard:manage-modules"})


@staff_required
def manage_lessons_view(request):
    lessons = Lesson.objects.select_related("module", "module__course").prefetch_related("resources")
    return render(request, "dashboard/manage_lessons.html", {"lessons": lessons})


@staff_required
def lesson_detail_admin_view(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("module", "module__course").prefetch_related("resources"),
        id=lesson_id,
    )
    return render(request, "dashboard/lesson_detail.html", {"lesson": lesson})


@staff_required
def create_lesson_view(request):
    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson created.")
            return redirect("dashboard:manage-lessons")
    else:
        form = LessonForm()
    return _render_wizard_form(request, form, "Create Lesson", LESSON_WIZARD_STEPS, "dashboard:manage-lessons")


@staff_required
def edit_lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated.")
            return redirect("dashboard:manage-lessons")
    else:
        form = LessonForm(instance=lesson)
    return _render_wizard_form(request, form, "Edit Lesson", LESSON_WIZARD_STEPS, "dashboard:manage-lessons")


@staff_required
def delete_lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == "POST":
        lesson.delete()
        messages.success(request, "Lesson deleted.")
        return redirect("dashboard:manage-lessons")
    return render(request, "dashboard/confirm_delete.html", {"item": lesson, "back_url": "dashboard:manage-lessons"})


@staff_required
def create_lesson_resource_view(request):
    if request.method == "POST":
        form = LessonResourceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson resource added.")
            return redirect("dashboard:manage-resources")
    else:
        form = LessonResourceForm()
    return _render_wizard_form(
        request,
        form,
        "Add Lesson Resource",
        RESOURCE_WIZARD_STEPS,
        "dashboard:manage-resources",
    )


@staff_required
def edit_lesson_resource_view(request, resource_id):
    resource = get_object_or_404(LessonResource, id=resource_id)
    if request.method == "POST":
        form = LessonResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson resource updated.")
            return redirect("dashboard:manage-resources")
    else:
        form = LessonResourceForm(instance=resource)
    return _render_wizard_form(
        request,
        form,
        "Edit Lesson Resource",
        RESOURCE_WIZARD_STEPS,
        "dashboard:manage-resources",
    )


@staff_required
def resource_detail_admin_view(request, resource_id):
    resource = get_object_or_404(
        LessonResource.objects.select_related("lesson", "lesson__module", "lesson__module__course"),
        id=resource_id,
    )
    return render(request, "dashboard/resource_detail.html", {"resource": resource})


@staff_required
def delete_lesson_resource_view(request, resource_id):
    resource = get_object_or_404(LessonResource, id=resource_id)
    if request.method == "POST":
        resource.delete()
        messages.success(request, "Lesson resource deleted.")
        return redirect("dashboard:manage-resources")
    return render(request, "dashboard/confirm_delete.html", {"item": resource, "back_url": "dashboard:manage-resources"})


@staff_required
def manage_resources_view(request):
    resources = LessonResource.objects.select_related("lesson", "lesson__module", "lesson__module__course")
    return render(request, "dashboard/manage_resources.html", {"resources": resources})


@staff_required
def manage_quizzes_view(request):
    quizzes = Quiz.objects.select_related("course").prefetch_related("questions")
    return render(request, "dashboard/manage_quizzes.html", {"quizzes": quizzes})


@staff_required
def create_quiz_view(request):
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Quiz created.")
            return redirect("dashboard:manage-quizzes")
    else:
        form = QuizForm()
    return _render_wizard_form(request, form, "Create Quiz", QUIZ_WIZARD_STEPS, "dashboard:manage-quizzes")


@staff_required
def edit_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, "Quiz updated.")
            return redirect("dashboard:manage-quizzes")
    else:
        form = QuizForm(instance=quiz)
    return _render_wizard_form(request, form, "Edit Quiz", QUIZ_WIZARD_STEPS, "dashboard:manage-quizzes")


@staff_required
def delete_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == "POST":
        quiz.delete()
        messages.success(request, "Quiz deleted.")
        return redirect("dashboard:manage-quizzes")
    return render(request, "dashboard/confirm_delete.html", {"item": quiz, "back_url": "dashboard:manage-quizzes"})


@staff_required
def create_question_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Question added.")
            return redirect("dashboard:manage-quizzes")
    else:
        form = QuestionForm(initial={"quiz": quiz})
    return _render_wizard_form(
        request,
        form,
        f"Add Question: {quiz.title}",
        QUESTION_WIZARD_STEPS,
        "dashboard:manage-quizzes",
    )


@staff_required
def edit_question_view(request, question_id):
    question = get_object_or_404(Question.objects.select_related("quiz"), id=question_id)
    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated.")
            return redirect("dashboard:manage-quizzes")
    else:
        form = QuestionForm(instance=question)
    return _render_wizard_form(request, form, "Edit Question", QUESTION_WIZARD_STEPS, "dashboard:manage-quizzes")


@staff_required
def delete_question_view(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted.")
        return redirect("dashboard:manage-quizzes")
    return render(request, "dashboard/confirm_delete.html", {"item": question, "back_url": "dashboard:manage-quizzes"})


@staff_required
def enrollment_list_view(request):
    enrollments = Enrollment.objects.select_related("user", "course").all()
    return render(request, "dashboard/enrollments.html", {"enrollments": enrollments})


@staff_required
def enrollment_detail_admin_view(request, enrollment_id):
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("user", "user__profile", "course"),
        id=enrollment_id,
    )
    return render(request, "dashboard/enrollment_detail.html", {"enrollment": enrollment})


@staff_required
def ai_logs_view(request):
    sessions = (
        ChatSession.objects.select_related("user", "course", "lesson")
        .prefetch_related("messages")
        .annotate(message_count=Count("messages"))
        .order_by("-updated_at")
    )
    sessions_with_messages = sessions.filter(message_count__gt=0)
    empty_sessions_count = sessions.filter(message_count=0).count()

    lesson_groups = {}
    total_messages_count = 0

    for session in sessions_with_messages:
        if session.lesson:
            group_key = f"lesson-{session.lesson_id}"
            lesson_label = session.lesson.title
            context_label = f"Course: {session.course.title}" if session.course else "Lesson Context"
        elif session.course:
            group_key = f"course-{session.course_id}"
            lesson_label = "Course-Level Chat"
            context_label = f"Course: {session.course.title}"
        else:
            group_key = "general"
            lesson_label = "General AI Tutor Context"
            context_label = "No specific lesson or course"

        if group_key not in lesson_groups:
            lesson_groups[group_key] = {
                "lesson_label": lesson_label,
                "context_label": context_label,
                "teachers": {},
                "total_messages": 0,
            }

        teacher_profile = getattr(session.user, "profile", None)
        teacher_name = (
            teacher_profile.full_name if teacher_profile and teacher_profile.full_name else session.user.username
        )
        teacher_key = session.user_id
        group = lesson_groups[group_key]

        if teacher_key not in group["teachers"]:
            group["teachers"][teacher_key] = {
                "teacher_name": teacher_name,
                "username": session.user.username,
                "sessions": [],
                "message_count": 0,
                "latest_at": session.updated_at,
            }

        messages = list(session.messages.all())
        message_count = len(messages)
        group["teachers"][teacher_key]["sessions"].append(
            {
                "title": session.title or "Session",
                "updated_at": session.updated_at,
                "messages": messages,
                "message_count": message_count,
            }
        )
        group["teachers"][teacher_key]["message_count"] += message_count
        if session.updated_at > group["teachers"][teacher_key]["latest_at"]:
            group["teachers"][teacher_key]["latest_at"] = session.updated_at

        group["total_messages"] += message_count
        total_messages_count += message_count

    grouped_logs = []
    for entry in lesson_groups.values():
        teachers = sorted(
            entry["teachers"].values(),
            key=lambda row: row["latest_at"],
            reverse=True,
        )
        grouped_logs.append(
            {
                "lesson_label": entry["lesson_label"],
                "context_label": entry["context_label"],
                "teachers": teachers,
                "teacher_count": len(teachers),
                "total_messages": entry["total_messages"],
            }
        )

    return render(
        request,
        "dashboard/ai_logs.html",
        {
            "grouped_logs": grouped_logs,
            "empty_sessions_count": empty_sessions_count,
            "total_sessions_count": sessions.count(),
            "sessions_with_messages_count": sessions_with_messages.count(),
            "lesson_group_count": len(grouped_logs),
            "total_messages_count": total_messages_count,
        },
    )
