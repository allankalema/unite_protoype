import json
import os
from urllib import error, request


def _build_prompt(user_message, course=None, lesson=None, history=None):
    history = history or []
    course_title = course.title if course else "General teacher development"
    module_title = lesson.module.title if lesson and lesson.module else "N/A"
    lesson_title = lesson.title if lesson else "N/A"
    lesson_summary = ""
    lesson_content = ""

    if lesson:
        lesson_summary = lesson.summary or ""
        lesson_content = lesson.content[:3500] if lesson.content else ""

    recent_history = "\n".join(
        [f"{item.get('role', 'user')}: {item.get('message', '')}" for item in history[-8:]]
    )

    return f"""
You are an AI tutor for Uganda National Institute for Teacher Education (UNITE).
Your role: patient, practical, and clear teacher-trainer assistant.

Rules:
- Keep explanations simple, structured, and classroom-relevant.
- Prefer bullet points and concrete examples for Uganda teacher contexts.
- If a direct answer is not in provided lesson/course context, explicitly say so.
- When context is missing, still give a helpful general explanation and suggest what to review.
- Avoid fabricating specific policy details.

Context:
Course: {course_title}
Module: {module_title}
Lesson: {lesson_title}
Lesson summary: {lesson_summary}
Lesson content excerpt:
{lesson_content}

Conversation history:
{recent_history}

Teacher question:
{user_message}
""".strip()


def generate_ai_response(user_message, course=None, lesson=None, history=None):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return (
            "AI tutor is not configured yet. Add GEMINI_API_KEY to your environment to enable live responses. "
            "For now, review the lesson summary and key objectives."
        )

    prompt = _build_prompt(user_message, course=course, lesson=lesson, history=history)
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 700,
        },
    }

    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=40) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            candidates = response_data.get("candidates", [])
            if not candidates:
                return "I could not generate a response right now. Please try again shortly."

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return "I could not generate a response right now. Please try again shortly."

            text_chunks = [part.get("text", "") for part in parts if part.get("text")]
            return "\n".join(text_chunks).strip() or "I could not generate a response right now."
    except error.HTTPError:
        return (
            "The AI tutor service is temporarily unavailable or the API key is invalid. "
            "Please verify GEMINI_API_KEY and try again."
        )
    except Exception:
        return "AI tutor encountered a connection issue. Please try again in a moment."
