from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from courses.models import Course, Enrollment, Lesson

from .forms import AIChatForm
from .models import ChatMessage, ChatSession
from .services import generate_ai_response


def _teacher_name(user):
    profile = getattr(user, "profile", None)
    if profile and profile.full_name:
        return profile.full_name.split()[0]
    return user.username


def _get_or_create_session(user, course=None, lesson=None, session_id=None):
    if session_id:
        return get_object_or_404(ChatSession, id=session_id, user=user)

    existing = ChatSession.objects.filter(user=user, course=course, lesson=lesson).first()
    if existing:
        return existing

    title = "General AI Tutor"
    if lesson:
        title = f"{lesson.title} Tutor"
    elif course:
        title = f"{course.title} Tutor"

    return ChatSession.objects.create(user=user, course=course, lesson=lesson, title=title)


@login_required
def ai_chat_view(request):
    course_id = request.GET.get("course_id")
    lesson_id = request.GET.get("lesson_id")
    session_id = request.GET.get("session_id")

    course = Course.objects.filter(id=course_id).first() if course_id else None
    lesson = Lesson.objects.select_related("module", "module__course").filter(id=lesson_id).first() if lesson_id else None

    if lesson:
        course = lesson.module.course

    if course and not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, "Enroll in the course first to use this tutor context.")
        return redirect("courses:detail", slug=course.slug)

    session = _get_or_create_session(request.user, course=course, lesson=lesson, session_id=session_id)
    chat_form = AIChatForm()

    return render(
        request,
        "ai_tutor/chat.html",
        {
            "session": session,
            "messages_list": session.messages.all(),
            "chat_form": chat_form,
            "course": session.course,
            "lesson": session.lesson,
        },
    )


@login_required
def ai_send_message_view(request):
    if request.method != "POST":
        return redirect("ai_tutor:chat")

    session_id = request.POST.get("session_id")
    session = get_object_or_404(
        ChatSession.objects.select_related("course", "lesson", "lesson__module"),
        id=session_id,
        user=request.user,
    )
    lesson_id = request.POST.get("lesson_id")
    if lesson_id and session.lesson_id and str(session.lesson_id) != str(lesson_id):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Chat session does not match the current lesson."}, status=400)
        messages.error(request, "Chat session does not match the current lesson.")
        return redirect("courses:lesson-detail", lesson_id=lesson_id)

    form = AIChatForm(request.POST)
    if not form.is_valid():
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Message is required."}, status=400)
        messages.error(request, "Please enter a message.")
        return redirect(f"{reverse('ai_tutor:chat')}?session_id={session.id}")

    user_message = form.cleaned_data["message"].strip()
    ChatMessage.objects.create(session=session, role=ChatMessage.ROLE_USER, message=user_message)

    history = list(session.messages.values("role", "message"))
    assistant_message = generate_ai_response(
        user_message=user_message,
        course=session.course,
        lesson=session.lesson,
        history=history,
        teacher_name=_teacher_name(request.user),
    )
    ai_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.ROLE_ASSISTANT,
        message=assistant_message,
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "user_message": user_message,
                "assistant_message": ai_msg.message,
                "session_id": session.id,
            }
        )

    return redirect(f"{reverse('ai_tutor:chat')}?session_id={session.id}")


@login_required
def chat_history_view(request):
    sessions = ChatSession.objects.filter(user=request.user).select_related("course", "lesson")
    return render(request, "ai_tutor/history.html", {"sessions": sessions})


@login_required
def clear_session_view(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)

    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return JsonResponse({"ok": True})
