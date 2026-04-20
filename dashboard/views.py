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
def create_course_view(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course created successfully.")
            return redirect("dashboard:manage-courses")
    else:
        form = CourseForm()
    return render(request, "dashboard/course_form.html", {"form": form, "title": "Create Course"})


@staff_required
def edit_course_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect("dashboard:manage-courses")
    else:
        form = CourseForm(instance=course)
    return render(request, "dashboard/course_form.html", {"form": form, "title": "Edit Course"})


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
def create_module_view(request):
    if request.method == "POST":
        form = ModuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Module created.")
            return redirect("dashboard:manage-modules")
    else:
        form = ModuleForm()
    return render(request, "dashboard/module_form.html", {"form": form, "title": "Create Module"})


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
    return render(request, "dashboard/module_form.html", {"form": form, "title": "Edit Module"})


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
def create_lesson_view(request):
    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson created.")
            return redirect("dashboard:manage-lessons")
    else:
        form = LessonForm()
    return render(request, "dashboard/lesson_form.html", {"form": form, "title": "Create Lesson"})


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
    return render(request, "dashboard/lesson_form.html", {"form": form, "title": "Edit Lesson"})


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
    return render(request, "dashboard/resource_form.html", {"form": form, "title": "Add Lesson Resource"})


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
    return render(request, "dashboard/resource_form.html", {"form": form, "title": "Edit Lesson Resource"})


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
    return render(request, "dashboard/quiz_form.html", {"form": form, "title": "Create Quiz"})


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
    return render(request, "dashboard/quiz_form.html", {"form": form, "title": "Edit Quiz"})


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
    return render(request, "dashboard/question_form.html", {"form": form, "title": f"Add Question: {quiz.title}"})


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
    return render(request, "dashboard/question_form.html", {"form": form, "title": "Edit Question"})


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
